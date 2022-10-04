from typing import Dict, Optional, Any
from numpy import array
from vedo import show, Plotter

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.VedoActor import VedoActor


class VedoVisualizer:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False):
        """
        Manage the creation, update and rendering of Vedo Actors.

        :param database: Database to connect to.
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        """

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
        self.__plotter: Optional[Plotter] = None
        self.__offscreen: bool = offscreen
        self.step: int = 0

    def get_database(self):
        """
        Get the Database.
        """

        return self.__database

    def get_actor(self,
                  actor_id: int):
        """
        Get an Actor instance.

        :param actor_id: Index of the Actor.
        """

        return self.__all_actors[str(actor_id)]

    def init_visualizer(self):
        """
        Initialize the Visualizer: create all Actors and render them in a Plotter.
        """

        # 1. Connect signals between the VedoFactory and the Visualizer
        table_names = self.__database.get_tables()
        self.__database.register_pre_save_signal(table_name='Sync',
                                                 handler=self.__sync_visualizer)
        self.__database.connect_signals()

        # 2. Retrieve visual data and create Actors (one Table per Actor)
        instances = {}
        table_names.remove('Visual')
        table_names.remove('Sync')
        for table_name in table_names:
            # Get the full line of data
            data_dict = self.__database.get_line(table_name=table_name,
                                                 joins='Visual')
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
            instances[at].append(self.__actors[at][actor_id].create(data_dict).apply_cmap(cmap_dict))

        # 3. Create Plotter if offscreen is False
        if not self.__offscreen:
            actors = []
            for window in sorted(instances.keys()):
                actors.append(instances[window])
            plt = show(actors,
                       new=True,
                       N=len(actors),
                       sharecam=True,
                       interactive=False,
                       title='SofaVedo',
                       axes=4)
            plt.addButton(plt.interactor.TerminateApp, states=["start"])
            plt.interactive()
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
        """
        Update an Actor instance with updated data.

        :param table_name: Name of the Table (one Table per Actor).
        :param data_dict: Updated data of the Actor.
        """

        if len(data_dict.keys()) > 1:
            # Sort data
            cmap_dict = {'scalar_field': data_dict.pop('scalar_field')} if 'scalar_field' in data_dict else {}
            # Get Actor instance
            actor = self.__all_actors[table_name.split('_')[1]]
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
        table_names.remove('Visual')
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
