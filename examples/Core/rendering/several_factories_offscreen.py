from vedo import Mesh
from numpy.random import random
from sys import argv

from SSD.Core.Storage import Database
from SSD.Core.Rendering import UserAPI, Replay


class Simulation:

    def __init__(self,
                 database: Database,
                 idx_instance: int):

        # Create the Mesh object
        self.mesh = Mesh('armadillo.obj')
        # Create a Factory and add the Mesh object
        self.factory = UserAPI(database=database,
                               idx_instance=idx_instance)
        self.factory.add_mesh(positions=self.mesh.vertices,
                              cells=self.mesh.cells,
                              at=idx_instance,
                              c='orange3' if idx_instance == 0 else 'blue3')

    def connect_to_visualizer(self):

        # Connect the Factory to the Visualizer
        self.factory.connect_visualizer(offscreen=True)

    def step(self):

        # Update the Mesh positions
        updated_positions = self.mesh.vertices + 0.1 * random(self.mesh.vertices.shape)
        self.factory.update_mesh(object_id=0,
                                 positions=updated_positions)
        self.factory.render()

    def close(self):

        # Close the Factory
        self.factory.close()


if __name__ == '__main__':

    # 1. Create a new Database
    db = Database(database_dir='my_databases',
                  database_name='several_factories_offscreen').new(remove_existing=True)

    # 2. Create several simulations
    nb_simu = 2
    simulations = [Simulation(database=db,
                              idx_instance=i) for i in range(nb_simu)]

    # 3. Connect each factory to a single offscreen Visualizer
    for simu in simulations:
        simu.connect_to_visualizer()

    # 4. Run a few steps (with possibly a different number of steps)
    for step in range(50):
        simulations[0].step()
        if step < 20:
            simulations[1].step()

    # 5. Close the Factories & Replay steps
    for simu in simulations:
        simu.close()
    Replay(database_dir='my_databases',
           database_name='several_factories_offscreen',
           backend='vedo' if len(argv) == 1 else argv[1]).launch()
