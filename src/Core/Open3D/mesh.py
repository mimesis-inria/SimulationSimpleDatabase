from vedo import Mesh
from numpy.random import random

from Open3dFactory import Open3dFactory
from Open3dVisualizer import Open3dVisualizer


# 1. Create the Factory, bind it to a new Database
factory = Open3dFactory(database_name='mesh',
                        remove_existing=True)

# 2. Add objects to the Factory, then launch the Visualizer
armadillo = Mesh('armadillo.obj')
factory.add_mesh(positions=armadillo.points(),
                 cells=armadillo.cells(),
                 c='green',
                 alpha=0.8,
                 scalar_field=armadillo.points()[:, 1])
Open3dVisualizer.launch(database_path=factory.get_path(),
                        offscreen=False,
                        fps=20)

# 3. Run a few steps
dofs = armadillo.points().shape
for step in range(100):
    factory.update_mesh(object_id=0,
                        positions=armadillo.points() + 0.1 * random(dofs))
    if step == 50:
        factory.update_mesh(object_id=0,
                            scalar_field=-1. * armadillo.points()[:, 1])
    factory.render()
factory.close()
