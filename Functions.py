import pandas as pd
import numpy as np
import geopy.distance
from geopy.distance import geodesic
import math
import Weather




def polarpandas(polar_csv):
    """ Convert polars csv to pandas dataframe
    Args: polar_csv (csv file)
    Output: polar_panda (pandas dataframe)
    """
    polars = pd.read_csv(polar_csv, sep = ';', index_col = 0)
    polars.columns = [float(c) for c in polars.columns]
    polars.index = [float(i) for i in polars.index]
    return polars

def find_distance(start_coords,end_coords):
    distance_nm = geodesic(start_coords,end_coords).nm
    return distance_nm

def rhumb_bearing(lat1, lon1, lat2, lon2):
    """ Returns constant bearing angle between two points

    """
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1

    # Handle crossing the anti-meridian
    if abs(dlon) > math.pi:
        dlon = dlon - math.copysign(2 * math.pi, dlon)

    dpsi = math.log(
        math.tan(math.pi / 4 + lat2 / 2) /
        math.tan(math.pi / 4 + lat1 / 2)
    )

    bearing = math.degrees(math.atan2(dlon, dpsi))
    return (bearing + 360) % 360

def bearing_to_north(latlon1, latlon2):
    """ Returns the true shortest direction, non constant bearing angle
    """
    lat1, lon1 = latlon1
    lat2, lon2 = latlon2
    # Convert degrees → radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1

    x = math.sin(dlon) * math.cos(lat2)
    y = (math.cos(lat1) * math.sin(lat2) -
         math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def get_twa(heading, twd):
    twa = (twd - heading + 180) % 360 - 180
    return twa

def find_speed(polars, tws, twa):
    twa = np.clip(twa, polars.index.min(), polars.index.max())
    tws = np.clip(tws, polars.columns.min(), polars.columns.max())

    twa_vals = polars.index.values
    tws_vals = polars.columns.values

    idx_low = np.searchsorted(twa_vals, twa) - 1
    idx_high = idx_low + 1

    idx_low = max(idx_low, 0)
    idx_high = min(idx_high, len(twa_vals) - 1)

    twa_low = twa_vals[idx_low]
    twa_high = twa_vals[idx_high]

    j_low = np.searchsorted(tws_vals, tws) - 1
    j_high = j_low + 1

    j_low = max(j_low, 0)
    j_high = min(j_high, len(tws_vals) - 1)

    tws_low, tws_high = tws_vals[j_low], tws_vals[j_high]

    V11 = polars.iloc[idx_low, j_low]   # lower TWS, lower TWA
    V12 = polars.iloc[idx_low, j_high]  # lower TWS, higher TWA
    V21 = polars.iloc[idx_high, j_low]  # higher TWS, lower TWA
    V22 = polars.iloc[idx_high, j_high] # higher TWS, higher TWA

    if twa_high == twa_low:
        V1, V2 = V11, V12
    else:
        V1 = V11 + (V21 - V11) * (twa - twa_low)/(twa_high - twa_low)
        V2 = V12 + (V22 - V12) * (twa - twa_low)/(twa_high - twa_low)

    if tws_high == tws_low:
        V = V1
    else:
        V = V1 + (V2 - V1) * (tws - tws_low)/(tws_high - tws_low)

    return V

def find_speed_at(polars, datetime, lat, lon, hdg):

    tws, twd = Weather.tws_twd(lat, lon, datetime)
    twa = abs(get_twa(hdg, twd))

    bsp = find_speed(polars, tws, twa)
    return bsp

def find_new_pos(cur_lat, cur_lon, hdg, dist_nm):
    new = geopy.distance.distance(meters = dist_nm * 1852).destination((cur_lat,cur_lon), bearing = hdg)
    return new.latitude, new.longitude

def find_time_to(polars, datetime, cur_lat, cur_lon, fut_lat, fut_lon):
    """ Find time between two points at starting points boatspeed

    Returns: time in minutes
    """
    hdg = rhumb_bearing(cur_lat, cur_lon, fut_lat, fut_lon)
    bsp = find_speed_at(polars, datetime, cur_lat, cur_lon, hdg)
    dist = find_distance((cur_lat, cur_lon) , (fut_lat, fut_lon))
    dt = dist / bsp * 60
    return dt

def indices_of_max_n(data_list, n):

    indices = range(len(data_list))
    sorted_indices = sorted(indices, key=lambda i: data_list[i], reverse=True)
    return sorted_indices[:n]




    

