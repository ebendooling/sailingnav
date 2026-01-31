import Functions as func
import folium
import numpy as np


def find_isochrone_line(polars, cur_time, lat, lon, h_step, dt=1):

    isochrone = []
    for hdg in range(0, 360, h_step):
        bsp = func.find_speed_at(polars, cur_time, lat, lon, hdg)

        if bsp <= 0:
            continue

        dist = bsp * dt

        pos = func.find_new_pos(lat, lon, hdg, dist)
        new_time = cur_time + np.timedelta64(int(dt*60), 'm')
        
        isochrone.append({
            'lat': pos[0],
            'lon': pos[1],
            'hdg': hdg,
            'bsp': bsp,
            'time': new_time
            })
    return isochrone


def find_limited_isochrone(polars, cur_time, lat, lon, dt, endlat, endlon, h_step, max_dev=60):
    isochrone = []
    end_bearing = func.rhumb_bearing(lat, lon, endlat, endlon)

    max_hdg = int(end_bearing + max_dev)
    min_hdg = int(end_bearing - max_dev)

    for hdg in range(min_hdg, max_hdg, h_step):
        bsp = func.find_speed_at(polars, cur_time, lat, lon, hdg)
        if bsp <= 0:
            continue

        dist = bsp * dt

        pos = func.find_new_pos(lat, lon, hdg, dist)
        new_time = cur_time + np.timedelta64(int(dt*60), 'm')
        
        isochrone.append({
            'lat': pos[0],
            'lon': pos[1],
            'hdg': hdg,
            'bsp': bsp,
            'time': new_time
            })
    return isochrone


def build_isochrones(polars, start_time, start_lat, start_lon,  endlat, endlon, dt_hours=6, h_step=30, max_dev=60, steps=5):
    isochrones = [find_isochrone_line(polars, start_time, start_lat, start_lon, h_step, dt=1)]
    cur_points = [{'lat': start_lat,'lon': start_lon,'time': start_time}]

    for step in range(steps-1):
        next_points = []
        N_KEEP = 100
        keep_steps = int(len(cur_points) / N_KEEP) + 5

        for point in cur_points[::keep_steps]:
            lat, lon, time = point['lat'], point['lon'], point['time']
            line = find_limited_isochrone(polars, time, lat, lon, dt_hours, endlat, endlon, h_step)
        
            next_points.extend(line)

        dists = [
        func.find_distance((start_lat, start_lon), (p['lat'], p['lon']))
        for p in next_points]

        keep_idx = func.indices_of_max_n(dists, N_KEEP)
        next_points = [next_points[i] for i in keep_idx]
        angles = [func.rhumb_bearing(start_lat, start_lon, p['lat'], p['lon']) for p in next_points]
        
        sorted_indices = sorted(range(len(next_points)), key=lambda i: angles[i])
        next_points = [next_points[i] for i in sorted_indices]

        isochrones.append(next_points)
        cur_points = next_points

    return isochrones


def iso_visualize(start, end, isochrones):
    m = folium.Map(location=start, zoom_start=6)
    
    for step_idx, isochrone in enumerate(isochrones):
        
        coords = [(p['lat'], p['lon']) for p in isochrone]
        folium.PolyLine(coords, color="blue", weight=3, opacity=0.7).add_to(m)

    folium.Marker(start, popup="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(end, popup="End", icon=folium.Icon(color="red")).add_to(m)
    m.save('route_map.html')