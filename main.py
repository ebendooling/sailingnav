import Functions as func
from datetime import datetime
import GridNavigation as GN

polars = func.polarpandas("j99polars.csv")
time = datetime.now()

start = (41.4918, -71.3119)
finish = (32.3078, -64.7505)



if __name__ == "__main__":
    nodes = GN.create_grid(start, finish, 5, 100)
    GN.grid_visualize(start, finish, nodes)
    