from vedo import Mesh
from numpy import arange
from numpy.random import random
from sys import argv

from SSD.Core.Rendering import UserAPI

# 1. Create the visualization API
factory = UserAPI(database_dir='my_databases',
                  database_name='visualization',
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
# 3.3. Add Arrows (object_id = 2)
factory.add_arrows(positions=mesh.vertices[:100],
                   vectors=mesh.vertex_normals[:100],
                   at=2,
                   res=15)
# 3.4. Add Markers (object_id = 3)
factory.add_markers(normal_to=0,
                    indices=arange(0, 10),
                    at=3,
                    size=1,
                    symbol='*')
# 3.5. Add Text (object_id = 4)
factory.add_text(content='0',
                 at=0,
                 corner='TL',
                 bold=True)

# 4. Initialize the visualization
factory.launch_visualizer(backend='vedo' if len(argv) == 1 else argv[1],
                          fps=20)

# # 5. Run a few steps
for step in range(100):
    updated_mesh = mesh.clone()
    updated_mesh.vertices = mesh.vertices + 0.1 * random(mesh.vertices.shape)
    # 5.1. Update the Mesh
    factory.update_mesh(object_id=0,
                        positions=updated_mesh.vertices)
    if step == 50:
        factory.update_mesh(object_id=0,
                            wireframe=True,
                            alpha=1.,
                            line_width=2.)
    # 5.2. Update the PointCloud
    factory.update_points(object_id=1,
                          positions=updated_mesh.vertices)
    if step == 50:
        factory.update_points(object_id=1,
                              alpha=0.5,
                              point_size=10,
                              scalar_field=mesh.vertices[:, 2])
    # 5.3. Update the Arrows
    factory.update_arrows(object_id=2,
                          positions=mesh.vertices[step:step + 100],
                          vectors=mesh.vertex_normals[step:step + 100])
    if step == 50:
        factory.update_arrows(object_id=2,
                              c='red')
    # 5.4. Update the Markers
    if step == 50:
        factory.update_markers(object_id=3,
                               alpha=0.5,
                               filled=False,
                               c='blue1',
                               symbol='o')
    # 5.5. Update the Text
    factory.update_text(object_id=4,
                        content=f'{step}')
    if step == 50:
        factory.update_text(object_id=4,
                            c='grey',
                            bold=False,
                            italic=True)

    # 5.6. Call a rendering step
    factory.render()

# 6. Close the visualization
factory.close()
