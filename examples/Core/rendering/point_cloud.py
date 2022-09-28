from vedo import Mesh
from numpy.random import random
from time import sleep

from SSD.Core.Rendering.VedoFactory import VedoFactory
from SSD.Core.Rendering.VedoVisualizer import VedoVisualizer


# 1. Create the rendering and the Factory, bind them to a new Database
visualizer = VedoVisualizer(database_name='point_cloud',
                            remove_existing=True)
factory = VedoFactory(database=visualizer.get_database())


# 2. Create the object to render
armadillo = Mesh('armadillo.obj')


# 3. Add objects to the Factory then init the rendering
factory.add_points(positions=armadillo.points(),
                   at=0, alpha=1., c='indigo', point_size=1)
factory.add_points(positions=armadillo.points(),
                   at=1, alpha=0.6, point_size=3, scalar_field=armadillo.points()[:, 1], colormap='gist_earth')
visualizer.init_visualizer()


# 4. Run a few step
dofs = armadillo.points().shape
for step in range(50):
    updated_positions = armadillo.points() + 0.1 * random(dofs)
    factory.update_points(object_id=0, positions=updated_positions, point_size=step // 10)
    if step == 25:
        factory.update_points(object_id=1, scalar_field=-1. * armadillo.points()[:, 1])
    visualizer.render()
    sleep(0.02)
