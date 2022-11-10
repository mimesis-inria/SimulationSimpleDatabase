from vedo import Mesh
from numpy.random import random, randint
from time import sleep

from SSD.Core.Rendering.VedoFactory import VedoFactory
from SSD.Core.Rendering.VedoVisualizer import VedoVisualizer


# 1. Create the rendering and the Factory, bind them to a new Database
visualizer = VedoVisualizer(database_name='markers',
                            remove_existing=True)
factory = VedoFactory(database=visualizer.get_database())


# 2. Create the object to render
armadillo = Mesh('armadillo.obj').compute_normals()


# 3. Add objects to the Factory then init the rendering
factory.add_mesh(positions=armadillo.points(), cells=armadillo.cells(),
                 at=0, alpha=0.4, c='blue7', wireframe=False, line_width=0.2)
factory.add_markers(normal_to=0, indices=randint(0, armadillo.npoints, 10),
                    at=0, symbol='*', size=0.3, c='orange4')
factory.add_markers(normal_to=0, indices=randint(0, armadillo.npoints, 10),
                    at=0, symbol='O', filled=False, size=0.5, c='red6')
visualizer.init_visualizer()


# 4. Run a few step
dofs = armadillo.points().shape
for step in range(50):
    updated_positions = armadillo.points() + 0.1 * random(dofs)
    factory.update_markers(object_id=1, indices=randint(0, armadillo.npoints, 10))
    factory.update_markers(object_id=2, indices=randint(0, armadillo.npoints, 10))
    visualizer.render()
    sleep(0.01)
