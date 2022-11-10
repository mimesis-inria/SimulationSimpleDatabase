from vedo import Mesh
from numpy import array
from numpy.random import random
from time import sleep

from SSD.Core.Rendering.VedoFactory import VedoFactory
from SSD.Core.Rendering.VedoVisualizer import VedoVisualizer


# 1. Create the rendering and the Factory, bind them to a new Database
visualizer = VedoVisualizer(database_name='symbols',
                            remove_existing=True)
factory = VedoFactory(database=visualizer.get_database())


# 2. Create the object to render
armadillo = Mesh('armadillo.obj').compute_normals()
fingers = array([30, 33, 63, 900, 1150, 1218, 1727, 2002])


# 3. Add objects to the Factory then init the rendering
factory.add_mesh(positions=armadillo.points(), cells=armadillo.cells(),
                 at=0, alpha=0.4, c='green3', wireframe=False, line_width=0.2)
factory.add_symbols(positions=armadillo.points()[fingers], orientations=array([1, 0, 0]),
                    at=0, symbol='0', size=0.3, c='orange4')
visualizer.init_visualizer()

# 4. Run a few steps
dofs = armadillo.points().shape
for step in range(50):
    updated_positions = armadillo.points() + 0.1 * random(dofs)
    factory.update_mesh(object_id=0, positions=updated_positions)
    factory.update_symbols(object_id=1, positions=updated_positions[fingers])
    visualizer.render()
    sleep(0.02)
