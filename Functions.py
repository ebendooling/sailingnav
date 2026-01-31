import pandas as pd
import numpy as np
import geopy.distance
from geopy.distance import geodesic
import math
import Weather


def polarpandas(polar_csv):
    """ Convert polars csv to pandas dataframe

    Args:
        polar_csv: csv file of a set of polars

    Returns:
        polars: pandas dataframe fo polars
    """
    polars = pd.read_csv(polar_csv, sep = ';', index_col = 0)
    polars.columns = [float(c) for c in polars.columns]
    polars.index = [float(i) for i in polars.index]
    return polars


def find_distance(start_coords,end_coords):
    """ Finds distance between two lat, lon coordinates

    Args:
        start_coords: starting coordinates tuple (lat,lon)
        end_coords: ending coordinates tuple (lat,lon)

    Returns:
        distance_nm: distance between points in nautical miles
    """
    distance_nm = geodesic(start_coords,end_coords).nm
    return distance_nm

def rhumb_bearing(lat1, lon1, lat2, lon2):
    """ Returns constant bearing angle between two points
    
    Args:
        lat1: float
        lon1: float
        lat2: float
        lon2: float
    
    Returns:
        bearing: constant bearing angle
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1

    # in case of anti-meridian
    if abs(dlon) > math.pi:
        dlon = dlon - math.copysign(2 * math.pi, dlon)

    dpsi = math.log(
        math.tan(math.pi / 4 + lat2 / 2) /
        math.tan(math.pi / 4 + lat1 / 2) )

    bearing = math.degrees(math.atan2(dlon, dpsi))
    return (bearing + 360) % 360


def get_twa(heading, twd):
    """ Gets twa from heading and twd
    
    Args:
        heading: float [0,360]
        twd: positive float
    
    Returns:
        twa: float [0,360]
    """
    twa = (twd - heading + 180) % 360 - 180
    return twa

def find_speed(polars, tws, twa):
    """ Interpolates speed at and instancee based off tws, twa, and polars
    
    Args:
        polars: pandas dataframe
        tws: positive float
        twa: float [0,360]
    
    Returns:
        twa: float [0,360]
    """
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

    V11 = polars.iloc[idx_low, j_low]
    V12 = polars.iloc[idx_low, j_high]
    V21 = polars.iloc[idx_high, j_low]
    V22 = polars.iloc[idx_high, j_high]

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
    """ Finds boatspeed at specific time and location
    
    Args:
        polars: pandas dataframe
        datetime: time in datetime format
        lat: float
        lon: float
        hdg: float [0,360]
    
    Returns:
        bsp: float boatspeed
    """
    tws, twd = Weather.tws_twd(lat, lon, datetime)
    twa = abs(get_twa(hdg, twd))

    bsp = find_speed(polars, tws, twa)
    return bsp


def find_new_pos(cur_lat, cur_lon, hdg, dist_nm):
    """ Finds new position in a specific distance and direction
    
    Args:
        cur_lat: float [0,360]
        cur_lon: float [0,360]
        hdg:  float heading
        dist_nm: desired distance away
    
    Returns:
        new position (lat, lon)
    """
    new = geopy.distance.distance(meters = dist_nm * 1852).destination((cur_lat,cur_lon), bearing = hdg)
    return new.latitude, new.longitude


def find_time_to(polars, datetime, cur_lat, cur_lon, fut_lat, fut_lon):
    """ Finds time between two points based on bsp at starting point
    
    Args:
        polars: pandas dataframe
        datetime: time in datetime format
        cur_lat: float
        cur_lon: float
        fut_lat: float
        fut_lon: float
        
    Returns:
        dt: time to travel between points
    """
    hdg = rhumb_bearing(cur_lat, cur_lon, fut_lat, fut_lon)
    bsp = find_speed_at(polars, datetime, cur_lat, cur_lon, hdg)
    dist = find_distance((cur_lat, cur_lon) , (fut_lat, fut_lon))
    dt = dist / bsp * 60
    return dt


def indices_of_max_n(data_list, n):
    """ Used to find indices of max n values in a list

    Args:
        data_list: list of floats
        n: int

    Returns:
        sorted_indices: list of n indices
    """
    indices = range(len(data_list))
    sorted_indices = sorted(indices, key=lambda i: data_list[i], reverse=True)
    return sorted_indices[:n]
