from vedo import Mesh
from numpy.random import random

from SSD.Core.Rendering.UserAPI import UserAPI
from SSD.Core.Rendering.Replay import Replay

# 1. Create the visualization API
factory = UserAPI(database_name='vedo_offscreen',
                  remove_existing=True)

# 2. Create the object to render
armadillo = Mesh('armadillo.obj')

# 3. Add objects to the Visualizer
# 3.1. Add a Mesh (object_id = 0)
factory.add_mesh(positions=armadillo.points(),
                 cells=armadillo.cells(),
                 at=0,
                 alpha=0.8,
                 c='orange6',
                 wireframe=False,
                 line_width=0.)
# 3.2. Add a PointCloud (object_id = 1)
factory.add_points(positions=armadillo.points(),
                   at=1,
                   point_size=5,
                   scalar_field=armadillo.points()[:, 1])

# 4. Initialize the visualization
factory.launch_visualizer(offscreen=True)

# 5. Run a few steps
for step in range(100):
    updated_armadillo = armadillo.clone().points(armadillo.points() + 0.1 * random(armadillo.points().shape))
    # 5.1. Update the Mesh
    factory.update_mesh(object_id=0,
                        positions=updated_armadillo.points())
    # 5.2. Update the PointCloud
    factory.update_points(object_id=1,
                          positions=updated_armadillo.points())
    # 5.3. Call a rendering step
    factory.render()

# 6. Close the visualization, replay steps
factory.close()
Replay(database_name='vedo_offscreen',
       backend='vedo').launch()
