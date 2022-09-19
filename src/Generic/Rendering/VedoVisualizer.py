from typing import Dict, Optional, Any
from numpy import array
from SSD.Generic.Storage.Database import Database

from SSD.Generic.Rendering.VedoActor import VedoActor

from vedo import show, Plotter


class VedoVisualizer:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_name: Optional[str] = None,
                 remove_existing: Optional[bool] = False):

        # Define Database
        if database is not None:
            self.__database: Database = database
        elif database_name is not None:
            self.__database: Database = Database(database_name=database_name).new(remove_existing=remove_existing)
        else:
            raise ValueError("Both 'database' and 'database_name' are not defined.")

        # Information about all Factories / Actors
        self.__actors: Dict[int, Dict[int, VedoActor]] = {}
        self.__all_actors: Dict[str, VedoActor] = {}
        self.__updated_actors: Dict[str, bool] = {}
        self.__plotter: Optional[Plotter] = None

    def get_database(self):
        return self.__database

    def get_actor(self, actor_id):
        return self.__all_actors[str(actor_id)]

    def init_visualizer(self):

        # 1. Connect DB save signals between the VedoFactory and the Visualizer
        table_names = self.__database.get_tables()
        table_names.remove('Visual')
        table_names.remove('Sync')
        for table_name in table_names:
            if table_name != 'Visual':
                self.__database.register_post_save_signal(table_name=table_name,
                                                          handler=self.update_instance)
        self.__database.connect_signals()

        # 2. Retrieve visual data and create Actors (one Table per Actor)
        instances = {}
        for table_name in table_names:
            # Get the full line of data
            data_dict = self.__database.get_line(table_name=table_name,
                                                 joins='Visual')
            data_dict.pop('id')
            # Sort data
            visual_dict = data_dict.pop('visual_fk')
            cmap_dict = {}
            cmap_dict['colormap'] = visual_dict.pop('colormap') if 'colormap' in visual_dict else 'jet'
            cmap_dict['scalar_field'] = data_dict.pop('scalar_field') if 'scalar_field' in data_dict else array([])
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
        plt = show(actors,
                   new=True,
                   N=len(actors),
                   sharecam=True,
                   interactive=True,
                   title='SofaVedo',
                   axes=4)
        # Once the user closed the window, recreate a new Plotter
        camera = {'pos': plt.camera.GetPosition(),
                  'focalPoint': plt.camera.GetFocalPoint()}
        self.__plotter = show(actors,
                              new=True,
                              N=len(actors),
                              sharecam=True,
                              interactive=False,
                              title='SofaVedo',
                              axes=plt.axes,
                              camera=camera)

    def update_instance(self,
                        table_name: str,
                        data_dict: Dict[str, Any]):

        if len(data_dict.keys()) > 1:

            # Sort data
            cmap_dict = {'scalar_field': data_dict.pop('scalar_field')} if 'scalar_field' in data_dict else {}

            actor = self.__all_actors[table_name.split('_')[1]]
            if actor.actor_type in ['Arrows', 'Markers', 'Symbols']:
                self.__plotter.remove(actor.instance, at=actor.at)
            actor.update(data_dict).apply_cmap(cmap_dict)
            if actor.actor_type in ['Arrows', 'Markers', 'Symbols']:
                self.__plotter.add(actor.instance, at=actor.at)
            self.__updated_actors[table_name.split('_')[1]] = True

    def render(self):

        self.__database.add_data(table_name='Sync',
                                 data={'step': 1})
        self.__plotter.render()
        table_names = self.__database.get_tables()
        table_names.remove('Visual')
        table_names.remove('Sync')
        for table_name in table_names:
            actor_id = table_name.split('_')[1]
            if self.__updated_actors[actor_id]:
                self.__updated_actors[actor_id] = False
            else:
                self.__database.add_data(table_name=table_name,
                                         data={})
