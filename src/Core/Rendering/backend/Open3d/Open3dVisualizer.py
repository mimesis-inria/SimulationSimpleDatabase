from typing import Dict, Optional, Tuple, List
from threading import Thread
from struct import unpack
from copy import copy
from time import time, sleep
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import open3d as o3d

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseVisualizer import BaseVisualizer
from SSD.Core.Rendering.backend.Open3d.Open3dActor import Open3dActor
from SSD.Core.Rendering.backend.Open3d.Open3dBaseApp import BaseApp


class Open3dVisualizer(BaseApp, BaseVisualizer):

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False,
                 fps: int = 20):
        """
        The Open3dVisualizer is used to manage the creation, update and rendering of Open3D Actors.

        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        """

        BaseVisualizer.__init__(self,
                                database=database,
                                database_dir=database_dir,
                                database_name=database_name,
                                remove_existing=remove_existing,
                                offscreen=offscreen,
                                fps=fps)

        # Define Database
        if database is not None:
            self.__database: Database = database
        else:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)

        # Information about Actors
        self.__actors: Dict[int, Dict[str, Open3dActor]] = {}
        self.__groups: Dict[str, int] = {}
        self.__current_group: int = 0
        self.__previous_group: int = 0
        self.__group_change: bool = False

        # Information about the Plotter
        self.__offscreen: bool = offscreen
        self.__fps: float = 1 / min(max(1, abs(fps)), 50)

        # Synchronization with the Factory
        self.__step: Tuple[int, int] = (1, 1)
        self.__is_done: List[bool] = []
        self.__socket: Optional[socket] = None
        self.__clients: List[socket] = []
        self.__requests: List[Tuple[int, int]] = []

    def get_database(self) -> Database:
        """
        Get the Database instance.
        """

        return self.__database

    def get_database_path(self) -> Tuple[str]:
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

    def init_visualizer(self,
                        nb_clients: int) -> None:
        """
        Initialize the Visualizer: create all Actors and render them in a Plotter.

        :param nb_clients: Number of Factories to connect to.
        """

        # 1. Connect to the Factory for synchronization
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.__socket.bind(('localhost', 20000))
        self.__socket.listen()
        clients = {}
        for _ in range(nb_clients):
            client, _ = self.__socket.accept()
            idx_client: int = unpack('i', client.recv(4))[0]
            clients[idx_client] = client
        for idx_client in sorted(clients.keys()):
            self.__clients.append(clients[idx_client])
            self.__is_done.append(False)

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
            if actor_type == 'Markers':
                object_data['normal_to'] = self.get_actor(object_data['normal_to'])
            elif actor_type == 'Text':
                self.additional_labels[table_name] = self.__actors[group][table_name]
            self.__actors[group][table_name].create(data=object_data)
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

        # 5. Create Visualizer if not offscreen
        if not self.__offscreen:

            # 5.1. Init Visualizer instance
            self._create_settings(len(self.__actors))
            self._window.set_on_close(self._exit)

            # 5.2 Add all Text
            for actor in self.additional_labels.values():
                self._window.add_child(actor.instance)
                actor.instance.visible = False

            # 5.3. Add geometries to the Visualizer
            for actor in self.__actors[self.__current_group].values():
                if actor.type == 'Text':
                    actor.instance.visible = True
                else:
                    self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)
            bounds = self._scene.scene.bounding_box
            self._scene.setup_camera(60, bounds, bounds.get_center())

            # 5.4. Launch mainloop
            if nb_clients == 1:
                Thread(target=self.__single_client_thread).start()
                self.__clients[0].send(b'done')
            else:
                for i, client in enumerate(self.__clients):
                    Thread(target=self.__listen_client, args=(i,)).start()
                    client.send(b'done')
                Thread(target=self.__multiple_clients_thread).start()

            o3d.visualization.gui.Application.instance.run()

    def __listen_client(self, idx_client: int):

        while not self.__is_done[idx_client]:
            msg = self.__clients[idx_client].recv(4)
            if len(msg) == 0:
                pass
            elif msg == b'exit':
                self.__is_done[idx_client] = True
                self._exit(force_quit=False)
            else:
                step = unpack('i', msg)[0]
                self.__requests.append((idx_client, step))

    def __multiple_clients_thread(self) -> None:

        # 2. Render at each Factory.render() call
        while False in self.__is_done:

            if len(self.__requests) > 0:
                self.__step = self.__requests.pop(0)

                if not self.__offscreen:
                    process_time = time()
                    o3d.visualization.gui.Application.instance.post_to_main_thread(self._window,
                                                                                   self.__update_instances)
                    # Respect frame rate
                    dt = max(0., self.__fps - (time() - process_time))
                    sleep(dt)

        # 3. Close the Visualizer
        if not self.__offscreen:
            o3d.visualization.gui.Application.instance.quit()

    def __single_client_thread(self):

        while not self.__is_done[0]:
            msg = self.__clients[0].recv(4)
            if len(msg) == 0:
                pass
            elif msg == b'exit':
                self.__is_done[0] = True
                self._exit(force_quit=False)
            else:
                self.__step = (0, unpack('i', msg)[0])
                if not self.__offscreen:
                    process_time = time()
                    o3d.visualization.gui.Application.instance.post_to_main_thread(self._window,
                                                                                   self.__update_instances)
                    # Respect frame rate
                    dt = max(0., self.__fps - (time() - process_time))
                    sleep(dt)

        # 3. Close the Visualizer
        if not self.__offscreen:
            o3d.visualization.gui.Application.instance.quit()

    def __update_instances(self) -> None:

        idx_factory, step = copy(self.__step)

        # 1. If the group ID changed, change the visibility of Actors
        if self.__group_change:
            self.__group_change = False
            # Remove previous group
            for table_name in self.__actors[self.__previous_group].keys():
                actor = self.get_actor(table_name)
                if actor.type == 'Text':
                    actor.instance.visible = False
                else:
                    self._scene.scene.remove_geometry(actor.name)
            # Add new group
            for table_name in self.__actors[self.__current_group].keys():
                actor = self.get_actor(table_name)
                if actor.type == 'Text':
                    actor.instance.visible = True
                else:
                    self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)

        # 2. Update all the Actors
        for group_id in self.__actors.keys():
            for table_name in self.__actors[group_id].keys():
                if f'_{idx_factory}_' in table_name:

                    # 2.1. Get the current step line in the Table
                    object_data = self.__database.get_line(table_name=table_name,
                                                           line_id=step)
                    object_data = dict(filter(lambda item: item[1] is not None, object_data.items()))

                    # 2.2. If the line contains fields, the Actor was updated, then update it
                    object_data.pop('id')
                    if len(object_data.keys()) > 0 or 'Markers' in table_name:
                        # Update Actor instance
                        actor = self.get_actor(table_name)
                        if actor.type == 'Markers' and 'normal_to' in object_data.keys():
                            object_data['normal_to'] = self.get_actor(object_data['normal_to'])
                        actor.update(data=object_data)
                        # Update the geometry in the Visualizer
                        if group_id == self.__current_group:
                            if actor.type == 'Text':
                                pass
                            else:
                                self._scene.scene.remove_geometry(actor.name)
                                self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)

        # 3. Done
        self.__clients[idx_factory].send(b'done')

    def _exit(self,
              force_quit: bool = True) -> None:

        if force_quit:
            for i, client in enumerate(self.__clients):
                client.send(b'exit')
                self.__is_done[i] = True

        if False not in self.__is_done:

            # Close the socket
            if self.__socket is not None:
                self.__socket.close()
                self.__socket = None

    def _change_group(self,
                      index: int) -> None:

        if index != self.__current_group:
            self.__previous_group = self.__current_group
            self.__current_group = index
            self.__group_change = True
