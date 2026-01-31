import Functions as func
import folium
import numpy as np
import heapq
import math

open_set_heap = []
count = 0

def grid_visualize(start, end, nodes):
    m = folium.Map(location=start, zoom_start=6)

    for row in nodes:
        for node in row:
            folium.CircleMarker(
            location=(float(node['position'][0]), float(node['position'][1])),
            radius=.01,
            color="black",
            fill=True,
            fillColor="black",
            fillOpacity="1.0"
            ).add_to(m)
    folium.Marker(start, popup="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(end, popup="End", icon=folium.Icon(color="red")).add_to(m)
    m.save('route_grid.html')



def create_node(position, g = 10000000, h = 0.0, parent = None):

    return {
        'position': position,
        'g': int(g), # cost so far
        'h': int(h), # heuristic cost to end
        'f': int(g + h), # total estimated cost
        'parent': parent, # where it came from
        'neighbors': []
    }

def get_lowest_f_node(node_list):
    if not node_list:
        return None
    return min(node_list, key=lambda node: node['f'])

def get_valid_neighbors(nodes, lon_idx, lat_idx):
    """
    Get the neighbors for a single node at the given grid indices.
    
    nodes: 2D grid of all nodes
    lon_idx: index in the outer list (longitude/column index)
    lat_idx: index in the inner list (latitude/row index)
    
    Returns: list of neighbor nodes
    """
    num_lons = len(nodes)
    num_lats = len(nodes[0]) if num_lons > 0 else 0
    

    directions = [ (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1) ]
    
    neighbors = []
    
    for dlon_idx, dlat_idx in directions:
        neighbor_lon_idx = lon_idx + dlon_idx
        neighbor_lat_idx = lat_idx + dlat_idx
        
        if (0 <= neighbor_lon_idx < num_lons and 0 <= neighbor_lat_idx < num_lats):
            
            neighbor_node = nodes[neighbor_lon_idx][neighbor_lat_idx]
            neighbors.append(neighbor_node)
    
    return neighbors
    

def create_grid(start, end, padding=5, resolution=50):


    lat_min, lat_max = sorted([start[0], end[0]])
    lon_min, lon_max = sorted([start[1], end[1]])

    lat_step = (lat_max - lat_min) / resolution
    lon_step = (lon_max - lon_min) / resolution

    lat_min -= lat_step * padding
    lat_max += lat_step * padding
    lon_min -= lon_step * padding
    lon_max += lon_step * padding

    grid_size = resolution + (padding * 2) + 1
    lats = np.linspace(lat_min, lat_max, grid_size)
    lons = np.linspace(lon_min, lon_max, grid_size)


    nodes = []
    for lon in lons:
        node_row = [create_node((float(lat), float(lon))) for lat in lats]
        nodes.append(node_row)

    # find neighbors and add to each node
    for lat_idx in range(len(nodes)):
        for lon_idx in range(len(nodes[0])):
            
            neighbors = []
            
            for dlat in [-1, 0, 1]:
                for dlon in [-1, 0, 1]:

                    if dlat == 0 and dlon == 0:
                        continue
                    
                    
                    new_lat = lat_idx + dlat
                    new_lon = lon_idx + dlon
                    if (0 <= new_lat < len(nodes) and 
                        0 <= new_lon < len(nodes[0])):
                        neighbors.append((new_lat, new_lon))
            
            nodes[lon_idx][lat_idx]['neighbors'] = neighbors
            
    return nodes
    


def node_weight(node_a, node_b, polars, datetime):
    node_weight = func.find_time_to(polars, datetime, node_a[0], node_a[1], node_b[0], node_b[1])

    return node_weight





def push_node(node):
    global count
    # We push (f_score, tie_breaker, node)
    heapq.heappush(open_set_heap, (node['f'], count, node))
    count += 1

# 3. Function to get the lowest f-score node
def pop_lowest_f():
    # Heappop always returns the smallest element
    f_score, _, node = heapq.heappop(open_set_heap)
    return node


def reconstruct_path(current):
    path = []
    while current:
        path.append(current['position'])
        current = current['parent']
    return path



def astar(start, finish, dlat, dlon, padding=5, resolution=50):
    nodes = create_grid(start, finish, dlat, dlon, padding, resolution)
    start = nodes[padding][padding]
    finish = nodes[-(padding+1)][-(padding+1)]
    openList = [start]
    closedList = []

    start['g'] = 0
    start['h'] = func.find_distance(start, finish)
    start['f'] = start['g'] + start['h']


    while len(openList) > 0:
        current = pop_lowest_f(openList) # node with lowest f value
    
        if current == finish:
            return reconstruct_path()

        closedList += openList.pop(0)
        for neighbor in current['neighbors']:
            if neighbor in closedList:
                continue
            tentative_g = current['g'] + func.find_distance((current['position']), (nodes[neighbor[0]][neighbor[1]]['position']))

            if neighbor not in openList:
                openList.append(neighbor)
            elif tentative_g >= nodes[neighbor[0]][neighbor[1]]['g']:
                continue

            nodes[neighbor[0]][neighbor[1]]['parent'] = current
            nodes[neighbor[0]][neighbor[1]]['g'] = tentative_g
            nodes[neighbor[0]][neighbor[1]]['h'] = func.find_distance((nodes[neighbor[0]][neighbor[1]]['position']), (finish['position']))
            nodes[neighbor[0]][neighbor[1]]['f'] = nodes[neighbor[0]][neighbor[1]]['g'] + nodes[neighbor[0]][neighbor[1]]['h']


    
    return print("No path exists")







def create_hexagonal_grid(start, end, spacing_km):
    lat_min, lat_max = sorted([start[0], end[0]])
    lon_min, lon_max = sorted([start[1], end[1]])
    
    center_lat = (lat_min + lat_max) / 2
    

    dlat = spacing_km / 111.0
    dlon = spacing_km / (111.0 * math.cos(math.radians(center_lat)))
    
    row_height = dlat * math.sqrt(3) / 2

    col_width = dlon

    num_rows = int(np.ceil((lat_max - lat_min) / row_height)) + 1
    num_cols = int(np.ceil((lon_max - lon_min) / col_width)) + 1

    nodes = []
    node_lookup = {}
    
    for row in range(num_rows):
        for col in range(num_cols):

            lat = lat_min + row * row_height

            lon_offset = (col_width / 2) if row % 2 == 1 else 0
            lon = lon_min + col * col_width + lon_offset

            node = create_node((float(lat), float(lon)))
            node['grid_pos'] = (row, col)
            node['neighbors'] = []
            
            nodes.append(node)
            node_lookup[(row, col)] = node
    

    for node in nodes:
        row, col = node['grid_pos']
        
        if row % 2 == 0:
            neighbor_offsets = [
                (-1, -1),  # Upper left
                (-1, 0),   # Upper right
                (0, -1),   # Left
                (0, 1),    # Right
                (1, -1),   # Lower left
                (1, 0)     # Lower right
            ]
        else:
            neighbor_offsets = [
                (-1, 0),   # Upper left
                (-1, 1),   # Upper right
                (0, -1),   # Left
                (0, 1),    # Right
                (1, 0),    # Lower left
                (1, 1)     # Lower right
            ]
        
        for drow, dcol in neighbor_offsets:
            neighbor_pos = (row + drow, col + dcol)
            if neighbor_pos in node_lookup:
                node['neighbors'].append(node_lookup[neighbor_pos])
    
    return nodes, node_lookup


def find_closest_node_hex(node_lookup, target_lat, target_lon):
    min_distance = float('inf')
    closest_node = None
    
    for node in node_lookup.values():
        node_lat, node_lon = node['position']
        distance = ((node_lat - target_lat)**2 + (node_lon - target_lon)**2)**0.5
        
        if distance < min_distance:
            min_distance = distance
            closest_node = node
    
    return closest_node


nodes, node_lookup = create_hexagonal_grid((5, 9), (15, 15), spacing_km=10)

# Find start and end nodes
start_node = find_closest_node_hex(node_lookup, 5, 9)
end_node = find_closest_node_hex(node_lookup, 15, 15)

def grid_visualize_hex(start, end, nodes):
    m = folium.Map(location=start, zoom_start=6)

    for node in nodes:
        folium.Circle(
            location=node['position'],
            radius=500,
            color="black",
            fill=True,
            fillColor="black",
            fillOpacity=0.8
        ).add_to(m)
    
    folium.Marker(start, popup="Start", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(end, popup="End", icon=folium.Icon(color="red")).add_to(m)
    m.save('route_grid_hex.html')

grid_visualize_hex((5, 9), (15, 15), nodes)