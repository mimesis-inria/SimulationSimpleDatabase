from vedo import Mesh
from numpy import arange
from numpy.random import random

from SSD.Core.Rendering.UserAPI import UserAPI

# 1. Create the visualization API
visu = UserAPI(database_name='open3d_example',
               remove_existing=True)

# 2. Create the object to render
armadillo = Mesh('armadillo.obj')

# 3. Add objects to the Visualizer
# 3.1. Add a Mesh (object_id = 0)
visu.add_mesh(positions=armadillo.points(),
              cells=armadillo.cells(),
              at=0,
              alpha=0.8,
              c='orange6',
              wireframe=False,
              line_width=0.)
# 3.2. Add a PointCloud (object_id = 1)
visu.add_points(positions=armadillo.points(),
                at=1,
                point_size=5,
                scalar_field=armadillo.points()[:, 1])
# 3.3. Add Arrows (object_id = 2)
visu.add_arrows(positions=armadillo.points()[:100],
                vectors=armadillo.normals()[:100],
                at=2,
                res=15)
# 3.4. Add Markers (object_id = 3)
visu.add_markers(normal_to=0,
                 indices=arange(0, 10),
                 at=3,
                 size=1,
                 symbol='0')
# 3.5. Add Text (object_id = 4)
visu.add_text(content='0',
              at=0,
              corner='TL',
              bold=True)

# 4. Initialize the visualization
visu.launch_visualizer(backend='open3d',
                       fps=20)

# 5. Run a few steps
for step in range(100):
    updated_armadillo = armadillo.clone().points(armadillo.points() + 0.1 * random(armadillo.points().shape))
    # 5.1. Update the Mesh
    visu.update_mesh(object_id=0,
                     positions=updated_armadillo.points())
    if step == 50:
        visu.update_mesh(object_id=0,
                         wireframe=True,
                         alpha=1.,
                         line_width=2.)
    # 5.2. Update the PointCloud
    visu.update_points(object_id=1,
                       positions=updated_armadillo.points())
    if step == 50:
        visu.update_points(object_id=1,
                           alpha=0.5,
                           point_size=10,
                           scalar_field=armadillo.points()[:, 2])
    # 5.3. Update the Arrows
    visu.update_arrows(object_id=2,
                       positions=armadillo.points()[step:step+100],
                       vectors=armadillo.normals()[step:step+100])
    if step == 50:
        visu.update_arrows(object_id=2,
                           c='red')
    # 5.4. Update the Markers
    if step == 50:
        visu.update_markers(object_id=3,
                            alpha=0.5,
                            filled=False,
                            c='blue1',
                            symbol='o')
    # 5.5. Update the Text
    visu.update_text(object_id=4,
                     content=f'{step}')
    if step == 50:
        visu.update_text(object_id=4,
                         c='grey',
                         bold=False,
                         italic=True)

    # 5.6. Call a rendering step
    visu.render()

# 6. Close the visualization
visu.close()
