from time import time, sleep
from typing import Optional, Dict, Tuple
from threading import Thread
from subprocess import run
from sys import executable, argv
import open3d as o3d
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from struct import unpack
from inspect import stack, getmodule

from SSD.Core.Storage.Database import Database
from Open3dActor import Open3dActor


class Open3dVisualizer:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False,
                 fps: int = 20):
        """
        Manage the creation, update and rendering of Open3D Actors.

        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        """

        # Define the Database
        if database is not None:
            self.__database: Database = database
        elif database_name is not None:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)
        else:
            raise ValueError("Both 'database' and 'database_name' are not defined.")

        # Information about Actors
        self.__actors: Dict[int, Dict[str, Open3dActor]] = {}
        self.__groups: Dict[str, int] = {}
        self.__current_group: int = 0
        self.__plotter: Optional[o3d.visualization.O3DVisualizer] = None
        self.__offscreen: bool = offscreen
        self.__fps: float = 1 / min(max(1, abs(fps)), 50)

        self.__step: int = 1
        self.__is_done = False

        self.__socket: Optional[socket] = None

    @staticmethod
    def launch(database_path: Tuple[str, str],
               offscreen: bool = False,
               fps: int = 20):
        """
        Launch the Open3dVisualizer in a new process to keep it interactive.

        :param database_path: Path to the Database to connect to.
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        """

        # Launch a new process
        t = Thread(target=Open3dVisualizer.__launch, args=(database_path, offscreen, fps,))
        t.start()

        # Connect to the Factory, wait for the Visualizer to be ready
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.connect(('localhost', 20000))
        sock.send(b'L')
        sock.recv(1)
        sock.close()

    @staticmethod
    def __launch(database_path: Tuple[str, str],
                 offscreen: bool,
                 fps: int):

        run([executable, __file__, f'{database_path[0]}%%{database_path[1]}', str(offscreen), str(fps)])

    def get_database(self):
        """
        Get the Database instance.
        """

        return self.__database

    def get_path(self):
        """
        Get the path to the Database.
        """

        return self.__database.get_path()

    def get_actor(self,
                  actor_name: str) -> Open3dActor:
        """
        Get an Actor instance.

        :param actor_name: Name of the Actor.
        """

        group = self.__groups[actor_name]
        return self.__actors[group][actor_name]

    def init_visualizer(self):
        """
        Initialize the Visualizer: create all Actors and render them in a Plotter.
        """

        # 0. Check that the Open3D Visualizer was launched with the self.launch() method
        if getmodule(stack()[-1][0]).__file__ != __file__:
            quit(print("Warning: The Open3dVisualizer should be launched with the 'launch' method."
                       "Check usage in documentation."))

        # 1. Connect to the Factory for synchronization
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.__socket.connect(('localhost', 20000))

        # 2. Sort the Tables names per factory and per object indices
        table_names = self.__database.get_tables()
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

        # 3. Retrieve visual data and create Actors (one Table per Actor)
        pre_groups = {}
        for table_name in sorted_table_names:

            # 3.1. Get the full line of data
            object_data = self.__database.get_line(table_name=table_name)
            object_data.pop('id')
            group = object_data.pop('at')

            # 3.2. Retrieve the good indexing of Actors
            actor_type = table_name.split('_')[0]
            if group not in self.__actors:
                self.__actors[group] = {}
                pre_groups[group] = []

            # 3.3. Create the Actor
            self.__actors[group][table_name] = Open3dActor(actor_type=actor_type,
                                                           actor_name=table_name,
                                                           actor_group=group)
            self.__actors[group][table_name].create(object_data=object_data)
            self.__groups[table_name] = group
            pre_groups[group].append(table_name)

        # 4. Update the group values
        for i, group in enumerate(sorted(self.__actors.keys())):

            # 4.1. Update the Database
            if i != group:
                for table_name in pre_groups[group]:
                    self.__database.update(table_name=table_name,
                                           data={'at': i})
            # 4.2. Update the Actors
            self.__actors[i] = self.__actors.pop(group)
            for idx, actor in self.__actors[group].items():
                actor.group = i
                self.__groups[idx] = i

        # 5.a. Create Visualizer if not offscreen
        if not self.__offscreen:

            # 5.1. Init Visualizer instance
            app = o3d.visualization.gui.Application.instance
            app.initialize()

            self.__plotter = o3d.visualization.O3DVisualizer()
            self.__plotter.set_on_close(self.__exit)
            self.__plotter.add_action("Change group", self.__change_group)

            # 5.2. Add geometries to the Visualizer
            for actor in self.__actors[self.__current_group].values():
                self.__plotter.add_geometry(actor.name, actor.instance, actor.material)
            self.__plotter.reset_camera_to_default()

            # 5.3. Launch mainloop
            app.add_window(self.__plotter)
            # Todo: deal with menu
            app.menubar = o3d.visualization.gui.Menu()
            Thread(target=self.__update_thread).start()
            app.run()

        # 5.b. Synchronize the Visualizer and the Factory if offscreen
        else:
            Thread(target=self.__update_thread).start()

    def __update_thread(self):

        # 1. The Visualizer is ready, synchronize with the Factory
        self.__socket.send(b'V')
        self.__socket.recv(1)

        # 2. Render at each Factory.render() call
        while not self.__is_done:
            msg = self.__socket.recv(4)
            # Exit command
            if msg == b'exit':
                self.__exit()
            # Render command (within step number)
            elif unpack('i', msg)[0] != self.__step:
                self.__step += 1
                if not self.__offscreen:
                    process_time = time()
                    o3d.visualization.gui.Application.instance.post_to_main_thread(self.__plotter,
                                                                                   self.__update_instances)

                    dt = max(0., self.__fps - (time() - process_time))
                    sleep(dt)
                else:
                    self.__update_offscreen()

        # 3. Close the Visualizer
        if not self.__offscreen:
            o3d.visualization.gui.Application.instance.quit()

    def __update_instances(self):

        for table_name in self.__actors[self.__current_group].keys():
            # Get the current step line in the Table
            object_data = self.__database.get_line(table_name=table_name,
                                                   line_id=self.__step)
            # If the ID of the line is correct, the Actor was updated
            if object_data.pop('id') == self.__step:
                if len(object_data.keys()) > 1:
                    # Update Actor instance
                    actor = self.get_actor(table_name)
                    actor.update(object_data=object_data)
                    # Update the geometry in the Visualizer
                    is_visible = self.__plotter.get_geometry(actor.name).is_visible
                    self.__plotter.remove_geometry(actor.name)
                    self.__plotter.add_geometry(actor.name, actor.instance, actor.material,
                                                is_visible=is_visible)
            # Otherwise, the Actor was not updated, then add an empty line
            else:
                self.__database.add_data(table_name=table_name,
                                         data={})

    def __update_offscreen(self):

        for table_name in self.__database.get_tables():
            # Get the current step line in the Table
            object_data = self.__database.get_line(table_name=table_name,
                                                   line_id=self.__step)
            # If the ID of the line mismatches, the Actor was not updated, then add an empty line
            if object_data.pop('id') != self.__step:
                self.__database.add_data(table_name=table_name,
                                         data={})

    def __change_group(self, vis):

        o3d.visualization.gui.Application.instance.post_to_main_thread(self.__plotter,
                                                                       self.__update_instances_group)

    def __update_instances_group(self):

        for table_name in self.__actors[self.__current_group].keys():
            actor = self.get_actor(table_name)
            self.__plotter.remove_geometry(actor.name)

        self.__current_group = (self.__current_group + 1) % len(self.__groups.keys())

        for table_name in self.__actors[self.__current_group].keys():
            actor = self.get_actor(table_name)
            self.__plotter.add_geometry(actor.name, actor.instance, actor.material)

    def __exit(self):

        self.__is_done = True
        return True


if __name__ == '__main__':

    db_path = argv[1].split('%%')
    db = Database(database_dir=db_path[0],
                  database_name=db_path[1]).load()
    visualizer = Open3dVisualizer(database=db,
                                  offscreen=argv[2] == 'True',
                                  fps=int(argv[3]))
    visualizer.init_visualizer()
