import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from datetime import datetime


cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


def tws_twd(lat, lon, datetime):
    """ Access Open Meteo public weather API

    Args:
        lat: float
        lon: float
        datetime: datetime

    Returns:
        wind_speed_10m: float
        wind_direction_10m: float
    """
    time = pd.Timestamp(datetime).tz_convert("UTC") if pd.Timestamp(datetime).tzinfo else pd.Timestamp(datetime, tz="UTC")

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["wind_speed_10m", "wind_direction_10m"],
        "start_date": time.strftime("%Y-%m-%d"),
        "end_date": time.strftime("%Y-%m-%d"),
        "wind_speed_unit": "kn",
        "timezone": "UTC",
    }

    responses = openmeteo.weather_api(
        "https://api.open-meteo.com/v1/forecast",
        params=params
    )
    response = responses[0]

    hourly = response.Hourly()
    times = pd.to_datetime(hourly.Time(), unit="s", utc=True)

    wind_speed = hourly.Variables(0).ValuesAsNumpy()
    wind_dir = hourly.Variables(1).ValuesAsNumpy()

    df = pd.DataFrame({
        "time": times,
        "wind_speed_10m": wind_speed,
        "wind_direction_10m": wind_dir,
    })

    idx = (df["time"] - time).abs().idxmin()
    row = df.loc[idx]

    return row["wind_speed_10m"], row["wind_direction_10m"]
