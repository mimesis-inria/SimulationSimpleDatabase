from vedo import Mesh
from numpy.random import random
from sys import argv

from SSD.Core.Rendering import UserAPI, Replay

# 1. Create the visualization API
factory = UserAPI(database_dir='my_databases',
                  database_name='offscreen',
                  remove_existing=True)

# 2. Create the object to render
mesh = Mesh('armadillo.obj').compute_normals()

# 3. Add objects to the Visualizer
# 3.1. Add a Mesh (object_id = 0)
factory.add_mesh(positions=mesh.vertices,
                 cells=mesh.cells,
                 at=0,
                 alpha=0.8,
                 c='orange6',
                 wireframe=False,
                 line_width=0.)
# 3.2. Add a PointCloud (object_id = 1)
factory.add_points(positions=mesh.vertices,
                   at=1,
                   point_size=5,
                   scalar_field=mesh.vertices[:, 1])

# 4. Initialize the visualization
factory.launch_visualizer(offscreen=True)

# 5. Run a few steps
print('Running offscreen...')
for step in range(100):
    updated_mesh = mesh.clone()
    updated_mesh.vertices = mesh.vertices + 0.1 * random(mesh.vertices.shape)
    # 5.1. Update the Mesh
    factory.update_mesh(object_id=0,
                        positions=updated_mesh.vertices)
    # 5.2. Update the PointCloud
    factory.update_points(object_id=1,
                          positions=updated_mesh.vertices)
    # 5.3. Call a rendering step
    factory.render()

# 6. Close the visualization, replay steps
print('...then replay.')
factory.close()
Replay(database_dir='my_databases',
       database_name='offscreen',
       backend='vedo' if len(argv) == 1 else argv[1]).launch()
