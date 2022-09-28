from vedo import Mesh
from numpy.random import random
from time import sleep

from SSD.Core.Rendering.VedoFactory import VedoFactory
from SSD.Core.Rendering.VedoVisualizer import VedoVisualizer


# 1. Create the rendering and the Factory, bind them to a new Database
visualizer = VedoVisualizer(database_name='mesh',
                            remove_existing=True)
factory = VedoFactory(database=visualizer.get_database())


# 2. Create the object to render
armadillo = Mesh('armadillo.obj')


# 3. Add objects to the Factory then init the rendering
factory.add_mesh(positions=armadillo.points(), cells=armadillo.cells(),
                 at=0, alpha=0.6, c='red', wireframe=False, line_width=0.1)
factory.add_mesh(positions=armadillo.points(), cells=armadillo.cells(),
                 at=1, c='green', wireframe=True, line_width=1.)
factory.add_mesh(positions=armadillo.points(), cells=armadillo.cells(),
                 at=2, alpha=0.6, line_width=0.1, scalar_field=armadillo.points()[:, 1], colormap='jet')
factory.add_mesh(positions=armadillo.points(), cells=armadillo.cells(),
                 at=3, wireframe=True, line_width=1., scalar_field=armadillo.points()[:, 1], colormap='coolwarm')
visualizer.init_visualizer()


# 4. Run a few step
dofs = armadillo.points().shape
for step in range(50):
    updated_positions = armadillo.points() + 0.1 * random(dofs)
    for i in [0, 1]:
        factory.update_mesh(object_id=i, positions=updated_positions)
    if step == 25:
        for i in [2, 3]:
            factory.update_mesh(object_id=i, scalar_field=-1. * armadillo.points()[:, 1])
    visualizer.render()
    sleep(0.02)
