from typing import Optional, Dict, Tuple
from vedo import show, Plotter
from numpy import array, ndarray

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.VedoActor import VedoActor


class ReplayVisualizer:

    def __init__(self,
                 database_name: str,
                 database_dir: str = ''):
        """
        Replay a simulation from saved visual data.

        :param database_name: Name of the Database.
        :param database_dir: Directory of the Database.
        """

        # Load the Database
        self.__database = Database(database_dir=database_dir, database_name=database_name).load()

        # Information about all Factories / Actors
        self.__actors: Dict[int, Dict[Tuple[int, int], VedoActor]] = {}
        self.__all_actors: Dict[Tuple[int, int], VedoActor] = {}
        self.__updated_actors: Dict[Tuple[int, int], bool] = {}
        self.__plotter: Optional[Plotter] = None
        self.__nb_sample: Optional[int] = None

        # Init visualizer
        self.step = 1

    def init_visualizer(self):
        """
        Initialize the Visualizer: create all Actors and render them in a Plotter.
        """

        # 1. Get the Tables of the Database, sort their names per factory and per object indices
        table_names = self.__database.get_tables()
        table_names.remove('Sync')
        sorted_table_names = []
        sorter: Dict[int, Dict[int, str]] = {}
        for table_name in table_names:
            factory_id, table_id = table_name.split('_')[-2:]
            if int(factory_id) not in sorter:
                sorter[int(factory_id)] = {}
            sorter[int(factory_id)][int(table_id)] = table_name
        for factory_id in sorted(sorter.keys()):
            for table_id in sorted(sorter[factory_id].keys()):
                sorted_table_names.append(sorter[factory_id][table_id])

        # 2. Retrieve visual data and create Actors (one Table per Actor)
        instances = {}
        for table_name in sorted_table_names:
            # Get the number of sample
            if self.__nb_sample is None:
                self.__nb_sample = self.__database.nb_lines(table_name=table_name)
            # Get the full line of data
            data_dict = self.__database.get_line(table_name=table_name,
                                                 line_id=1)
            data_dict.pop('id')
            # Sort data
            cmap_dict = {'colormap': data_dict.pop('colormap') if 'colormap' in data_dict else 'jet',
                         'scalar_field': data_dict.pop('scalar_field') if 'scalar_field' in data_dict else array([])}
            at = data_dict.pop('at')
            # Retrieve good indexing of Actors
            actor_type, factory_id, actor_id = table_name.split('_')
            factory_id, actor_id = int(factory_id), int(actor_id)
            if at not in self.__actors:
                self.__actors[at] = {}
                instances[at] = []
            # Create Actor
            self.__actors[at][(factory_id, actor_id)] = VedoActor(self, actor_type, at)
            self.__all_actors[(factory_id, actor_id)] = self.__actors[at][(factory_id, actor_id)]
            self.__updated_actors[(factory_id, actor_id)] = False
            instances[at].append(self.__actors[at][(factory_id, actor_id)].create(data_dict).apply_cmap(cmap_dict))

        # 3. Create Plotter
        actors = []
        for window in sorted(instances.keys()):
            actors.append(instances[window])

        self.__plotter = show(actors,
                              new=True,
                              N=len(actors),
                              sharecam=True,
                              interactive=False,
                              title='SofaVedo',
                              axes=4)
        self.__plotter.timer_callback('create')
        self.__plotter.add_callback('Timer', self.__update)
        self.__plotter.add_button(self.__start, states=['start'])
        self.__plotter.interactive()

    def get_actor(self,
                  actor_id: ndarray):
        """
        Get an Actor instance.

        :param actor_id: Index of the Actor.
        """

        return self.__all_actors[tuple(actor_id)]

    def __start(self):

        self.step = 1

    def __update(self, _):

        self.step += 1
        if self.step < self.__nb_sample:

            # 1. Get the Tables of the Database
            table_names = self.__database.get_tables()
            table_names.remove('Sync')

            # 2. Retrieve visual data and create Actors (one Table per Actor)
            for table_name in table_names:
                # Get the full line of data
                data_dict = self.__database.get_line(table_name=table_name, line_id=self.step)
                data_dict.pop('id')
                # Sort data
                cmap_dict = {'scalar_field': data_dict.pop('scalar_field')} if 'scalar_field' in data_dict else {}
                # Update Actors
                _, factory_id, actor_id = table_name.split('_')
                factory_id, actor_id = int(factory_id), int(actor_id)
                actor = self.__all_actors[(factory_id, actor_id)]
                if actor.actor_type in ['Arrows', 'Markers', 'Symbols']:
                    self.__plotter.remove(actor.instance, at=actor.at)
                actor.update(data_dict).apply_cmap(cmap_dict)
                if actor.actor_type in ['Arrows', 'Markers', 'Symbols']:
                    self.__plotter.add(actor.instance, at=actor.at)

            # 3. Render
            self.__plotter.render()
