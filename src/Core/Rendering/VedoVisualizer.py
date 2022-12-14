from typing import Dict, Optional, Any, Tuple
from numpy import array, ndarray
from vedo import show, Plotter
from platform import system

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.VedoActor import VedoActor


class VedoVisualizer:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False):
        """
        Manage the creation, update and rendering of Vedo Actors.

        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        """

        # Define Database
        if database is not None:
            self.__database: Database = database
        elif database_name is not None:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)
        else:
            raise ValueError("Both 'database' and 'database_name' are not defined.")

        # Information about all Factories / Actors
        self.__actors: Dict[int, Dict[Tuple[int, int], VedoActor]] = {}
        self.__all_actors: Dict[Tuple[int, int], VedoActor] = {}
        self.__plotter: Optional[Plotter] = None
        self.__offscreen: bool = offscreen
        self.step: int = 0

        self.__database.create_table(table_name='Sync',
                                     storing_table=False,
                                     fields=('step', str))
        self.__database.register_post_save_signal(table_name='Sync',
                                                  handler=self.__sync_visualizer)

    def get_database(self):
        """
        Get the Database.
        """

        return self.__database

    def get_path(self):
        """
        Get the path to the Database.
        """

        return self.__database.get_path()

    def get_actor(self,
                  actor_id: ndarray):
        """
        Get an Actor instance.

        :param actor_id: Index of the Actor.
        """

        return self.__all_actors[tuple(actor_id)]

    def init_visualizer(self):
        """
        Initialize the Visualizer: create all Actors and render them in a Plotter.
        """

        # 1. Connect signals between the VedoFactory and the Visualizer
        self.__database.connect_signals()

        # 2. Sort the Table names per factory and per object indices
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

        # 3.  Retrieve visual data and create Actors (one Table per Actor)
        instances = {}
        real_at = {}
        for table_name in sorted_table_names:
            # Get the full line of data
            data_dict = self.__database.get_line(table_name=table_name)
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
                real_at[at] = []
            # Create Actor
            self.__actors[at][(factory_id, actor_id)] = VedoActor(self, actor_type, at)
            self.__all_actors[(factory_id, actor_id)] = self.__actors[at][(factory_id, actor_id)]
            instances[at].append(self.__actors[at][(factory_id, actor_id)].create(data_dict).apply_cmap(cmap_dict))
            real_at[at].append(table_name)

        # 4. Update the 'at' values
        for i, at in enumerate(sorted(self.__actors.keys())):
            # Update in the Database
            if i != at:
                for table_name in real_at[at]:
                    self.__database.update(table_name=table_name,
                                           data={'at': i})
            # Update in Actors container
            instances[i] = instances.pop(at)
            # Update in Actors
            for idx in self.__actors[at]:
                self.__all_actors[idx].at = i

        # 5. Create Plotter if offscreen is False
        if not self.__offscreen:
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
            self.__plotter.addButton(self.__plotter.interactor.TerminateApp, states=["start"])
            self.__plotter.interactive()
            # Once the user closed the window, recreate a new Plotter
            if system() != 'Darwin':
                camera = {'pos': self.__plotter.camera.GetPosition(),
                          'focalPoint': self.__plotter.camera.GetFocalPoint()}
                self.__plotter = show(actors,
                                      new=True,
                                      N=len(actors),
                                      sharecam=True,
                                      interactive=False,
                                      title='SofaVedo',
                                      axes=self.__plotter.axes,
                                      camera=camera)

    def update_instance(self,
                        table_name: str,
                        data_dict: Dict[str, Any]):
        """
        Update an Actor instance with updated data.

        :param table_name: Name of the Table (one Table per Actor).
        :param data_dict: Updated data of the Actor.
        """

        if len(data_dict.keys()) > 1:
            # Sort data
            cmap_dict = {'scalar_field': data_dict.pop('scalar_field')} if 'scalar_field' in data_dict else {}
            # Get Actor instance
            _, factory_id, actor_id = table_name.split('_')
            factory_id, actor_id = int(factory_id), int(actor_id)
            actor = self.__all_actors[(factory_id, actor_id)]
            # If Actor cannot be updated, remove from Plotter
            if actor.actor_type in ['Arrows', 'Markers', 'Symbols'] and not self.__offscreen:
                self.__plotter.remove(actor.instance, at=actor.at)
            # Update (or re-create) Actor, apply cmap
            actor.update(data_dict).apply_cmap(cmap_dict)
            # If Actor was re-created, add it to Plotter
            if actor.actor_type in ['Arrows', 'Markers', 'Symbols'] and not self.__offscreen:
                self.__plotter.add(actor.instance, at=actor.at)

    def render(self):
        """
        Render the current state of Actors in the Plotter.
        """

        self.step += 1
        self.__database.add_data(table_name='Sync',
                                 data={'step': 'V'})

    def __sync_visualizer(self, table_name, data_dict):

        # 0. Call to render from Factory
        if data_dict['step'] == 'F':
            self.step += 1

        # 1. Retrieve visual data and update Actors (one Table per Actor)
        table_names = self.__database.get_tables()
        table_names.remove('Sync')
        for table_name in table_names:
            # Get the current step line in the Table
            data_dict = self.__database.get_line(table_name=table_name,
                                                 line_id=self.step)
            # If the id of line is correct, the Actor was updated
            if data_dict.pop('id') == self.step:
                self.update_instance(table_name=table_name,
                                     data_dict=data_dict)
            # Otherwise, the actor was not updated, then add an empty line
            else:
                self.__database.add_data(table_name=table_name,
                                         data={})

        # 2. Render Plotter if offscreen is False
        if not self.__offscreen:
            self.__plotter.render()
