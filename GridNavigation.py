import Functions as func
import folium
import numpy as np



def grid_visualize(start, end, nodes):
    m = folium.Map(location=start, zoom_start=6)

    for row in nodes:
        for node in row:
            folium.CircleMarker(
            location=(float(node['position'][0]), float(node['position'][1])),
            radius=.1,
            color="black",
            fill=True,
            popup="Circle Marker"
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
    

def create_grid(start, end, dlat, dlon):


    lat_min, lat_max = sorted([start[0], end[0]])
    lon_min, lon_max = sorted([start[1], end[1]])

    lat_min -= 2.5
    lat_max += 2.5
    lon_min -= 2.5
    lon_max += 2.5

    lats = np.arange(lat_min, lat_max + dlat, dlat)
    lons = np.arange(lon_min, lon_max + dlon, dlon)

    nodes = []
    for lon in lons:
        node_row = [create_node((float(lat), float(lon))) for lat in lats]
        nodes.append(node_row)

    # find neighbors and add to each node
    for lon_idx in range(len(nodes)):
        for lat_idx in range(len(nodes[0])):
            
            neighbors = []
            
            for dlon in [-1, 0, 1]:
                for dlat in [-1, 0, 1]:

                    if dlon == 0 and dlat == 0:
                        continue
                    
                    new_lon = lon_idx + dlon
                    new_lat = lat_idx + dlat
                    if (0 <= new_lon < len(nodes) and 
                        0 <= new_lat < len(nodes[0])):
                        neighbors.append((new_lon, new_lat))
            
            nodes[lon_idx][lat_idx]['neighbors'] = neighbors
            
    return nodes
    



def node_weight(node_a, node_b, polars, datetime):
    node_weight = func.find_time_to(polars, datetime, node_a[0], node_a[1], node_b[0], node_b[1])

    return node_weight

#def reconstruct_path(goal_node):


nodes = create_grid((5,15),(15,15),.1,.1)
print(nodes)
grid_visualize((5,15),(15,15),nodes)

# def astar(start, finish):
#     openList = [start]
#     closedList = []

#     start.g = 0
#     start.h = func.find_distance(start, finish)
#     start.f = start.g + start.h
#     start.parent = None

#     while len(openList) > 0:
#         current = 