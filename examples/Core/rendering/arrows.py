from vedo import Mesh
from numpy import where
from numpy.random import random
from time import sleep

from SSD.Core.Rendering.VedoFactory import VedoFactory
from SSD.Core.Rendering.VedoVisualizer import VedoVisualizer


# 1. Create the rendering and the Factory, bind them to a new Database
visualizer = VedoVisualizer(database_name='arrows',
                            remove_existing=True)
factory = VedoFactory(database=visualizer.get_database())


# 2. Create the object to render
armadillo = Mesh('armadillo.obj').compute_normals()


# 3. Add objects to the Factory then init the rendering
min_y, max_y = armadillo.points()[:, 1].min(), armadillo.points()[:, 1].max()
selection = lambda s: where((armadillo.points()[:, 1] < max_y - s * ((max_y - min_y) / 5)) &
                            (armadillo.points()[:, 1] > min_y + (4 - s) * ((max_y - min_y) / 5)))
factory.add_arrows(positions=armadillo.points(), vectors=armadillo.normals(),
                   at=0, alpha=0.6, c='orange', res=5)
factory.add_arrows(positions=armadillo.points()[selection(0)], vectors=armadillo.normals()[selection(0)],
                   at=1, alpha=1., c='green', res=15)
visualizer.init_visualizer()


# 4. Run a few step
dofs = armadillo.points().shape
for step in range(50):
    updated_positions = armadillo.points() + 0.1 * random(dofs)
    factory.update_arrows(object_id=0, positions=updated_positions)
    if step % 10 == 0:
        factory.update_arrows(object_id=1, positions=armadillo.points()[selection(step // 10)],
                              vectors=armadillo.normals()[selection(step // 10)])
    visualizer.render()
    sleep(0.01)
