from vedo import Mesh
from numpy.random import random
from threading import Thread
from time import sleep, time

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.UserAPI import UserAPI
from SSD.Core.Rendering.Visualizer import Visualizer


class Simulation:

    def __init__(self,
                 database: Database,
                 idx_instance: int):
        self.idx_instance = idx_instance
        self.armadillo = Mesh('armadillo.obj')
        self.factory = UserAPI(database=database,
                               idx_instance=self.idx_instance)

    def create_visualization(self):
        self.factory.add_mesh(positions=self.armadillo.points(),
                              cells=self.armadillo.cells(),
                              at=self.idx_instance,
                              c='orange3' if self.idx_instance == 0 else 'blue3')
        self.factory.connect_visualizer()

    def step(self):
        updated_positions = self.armadillo.points() + 0.1 * random(self.armadillo.points().shape)
        self.factory.update_mesh(object_id=0,
                                 positions=updated_positions)
        self.factory.render()

    def close(self):
        self.factory.close()


if __name__ == '__main__':

    start = time()

    db = Database(database_name='several_factories').new(remove_existing=True)

    nb_simu = 2
    Visualizer.launch(backend='open3d',
                      database_name='several_factories',
                      nb_clients=nb_simu)

    simu = [Simulation(database=db,
                       idx_instance=i) for i in range(nb_simu)]

    th = []
    for s in simu:
        t = Thread(target=s.create_visualization)
        th.append(t)
        t.start()
    for t in th:
        t.join()

    for step in range(50):
        if step < 20:
            for s in simu:
                s.step()
        else:
            simu[0].step()

    for s in simu:
        s.close()

    print(time() - start)
