from typing import Optional, Dict
from vedo import show, Plotter
from numpy import array

from SSD.Generic.Storage.Database import Database
from SSD.Generic.Rendering.VedoActor import VedoActor


class ReplayVisualizer:

    def __init__(self,
                 database_name: str,
                 database_dir: str = '',
                 mode: str = 'auto'):
        # Load the Database
        self.__database = Database(database_dir=database_dir, database_name=database_name).load()

        # Information about all Factories / Actors
        self.__actors: Dict[int, Dict[int, VedoActor]] = {}
        self.__all_actors: Dict[str, VedoActor] = {}
        self.__updated_actors: Dict[str, bool] = {}
        self.__plotter: Optional[Plotter] = None
        self.__nb_sample: Optional[int] = None

        # Init visualizer
        self.mode = mode
        self.step = 1

    def init_visualizer(self):
        # 1. Get the Tables of the Database
        table_names = self.__database.get_tables()
        table_names.remove('Visual')
        table_names.remove('Sync')

        # 2. Retrieve visual data and create Actors (one Table per Actor)
        instances = {}
        for table_name in table_names:
            # Get the number of sample
            if self.__nb_sample is None:
                self.__nb_sample = self.__database.nb_lines(table_name=table_name)
            # Get the full line of data
            data_dict = self.__database.get_line(table_name=table_name,
                                                 joins='Visual',
                                                 line_id=1)
            data_dict.pop('id')
            # Sort data
            visual_dict = data_dict.pop('visual_fk')
            cmap_dict = {'colormap': visual_dict.pop('colormap') if 'colormap' in visual_dict else 'jet',
                         'scalar_field': data_dict.pop('scalar_field') if 'scalar_field' in data_dict else array([])}
            at = visual_dict.pop('at')
            # Retrieve good indexing of Actors
            actor_type, actor_id = table_name.split('_')
            if at not in self.__actors:
                self.__actors[at] = {}
                instances[at] = []
            # Create Actor
            self.__actors[at][actor_id] = VedoActor(self, actor_type, at)
            self.__all_actors[actor_id] = self.__actors[at][actor_id]
            self.__updated_actors[actor_id] = False
            instances[at].append(self.__actors[at][actor_id].create(data_dict).apply_cmap(cmap_dict))

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
        self.__plotter.timerCallback('create')
        self.__plotter.addCallback('Timer', self.mainloop)
        self.__plotter.addButton(self.start, states=['start'])
        self.__plotter.interactive()

    def start(self):
        self.step = 1

    def mainloop(self, event):

        self.step += 1
        if self.step < self.__nb_sample:

            # 1. Get the Tables of the Database
            table_names = self.__database.get_tables()
            table_names.remove('Visual')
            table_names.remove('Sync')

            # 2. Retrieve visual data and create Actors (one Table per Actor)
            for table_name in table_names:
                # Get the full line of data
                data_dict = self.__database.get_line(table_name=table_name, line_id=self.step)
                data_dict.pop('id')
                # Sort data
                cmap_dict = {'scalar_field': data_dict.pop('scalar_field')} if 'scalar_field' in data_dict else {}
                # Update Actors
                actor = self.__all_actors[table_name.split('_')[1]]
                if actor.actor_type in ['Arrows', 'Markers', 'Symbols']:
                    self.__plotter.remove(actor.instance, at=actor.at)
                actor.update(data_dict).apply_cmap(cmap_dict)
                if actor.actor_type in ['Arrows', 'Markers', 'Symbols']:
                    self.__plotter.add(actor.instance, at=actor.at)

            self.__plotter.render()
