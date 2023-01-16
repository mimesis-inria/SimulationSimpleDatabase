from typing import Dict, Optional, Any, Tuple
from threading import Thread
from subprocess import run
from sys import executable, argv
from struct import unpack
from copy import copy
from time import time, sleep
from numpy import array, ndarray
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from vedo import show, Plotter
from platform import system

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering._ressources.VedoActor import VedoActor
from SSD.Core.Rendering._ressources._Visualizer import _Visualizer


class VedoVisualizer(_Visualizer):

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False,
                 fps: int = 20):
        """
        Manage the creation, update and rendering of Vedo Actors.

        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        """

        _Visualizer.__init__(self, database=database, database_dir=database_dir, database_name=database_name,
                             remove_existing=remove_existing, offscreen=offscreen, fps=fps)

        # Define Database
        if database is not None:
            self.__database: Database = database
        else:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)

        # Information about Actors
        self.__actors: Dict[int, Dict[str, VedoActor]] = {}
        self.__groups: Dict[str, int] = {}
        self.__all_actors: Dict[str, VedoActor] = {}
        self.__plotter: Optional[Plotter] = None
        self.__offscreen: bool = offscreen
        self.__fps: float = 1 / min(max(1, abs(fps)), 50)

        self.__step: int = 0
        self.__is_done = False
        self.__socket: Optional[socket] = None
        self.__clients: List[socket] = []

    def get_database(self) -> Database:
        """
        Get the Database.
        """

        return self.__database

    def get_database_path(self) -> Tuple[str]:
        """
        Get the path to the Database.
        """

        return self.__database.get_path()

    def get_actor(self,
                  actor_name: str) -> VedoActor:
        """
        Get an Actor instance.

        :param actor_name: Name of the Actor.
        """

        group = self.__groups[actor_name]
        return self.__actors[group][actor_name]

    def init_visualizer(self,
                        nb_clients: int):
        """
        Initialize the Visualizer: create all Actors and render them in a Plotter.
        """

        # 1. Connect signals between the VedoFactory and the Visualizer
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.__socket.bind(('localhost', 20000))
        self.__socket.listen()
        for _ in range(nb_clients):
            client, _ = self.__socket.accept()
            self.__clients.append(client)

        # 2. Sort the Table names per factory and per object indices
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

        # 3.  Retrieve visual data and create Actors (one Table per Actor)
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
            self.__actors[group][table_name] = VedoActor(actor_type=actor_type,
                                                         actor_name=table_name,
                                                         actor_group=group)
            if actor_type == 'Markers':
                object_data['normal_to'] = self.get_actor(object_data['normal_to'])
            self.__actors[group][table_name].create(data=object_data)
            self.__groups[table_name] = group
            pre_groups[group].append(table_name)

        # 4. Update the group values
        for i, group in enumerate(sorted(self.__actors.keys())):

            # 4.1. Update in the Database
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
            actors = []
            for group in self.__actors.keys():
                actors.append([])
                for actor in self.__actors[group].values():
                    actors[-1].append(actor.instance)
            self.__plotter = show(actors,
                                  new=True,
                                  N=len(actors),
                                  sharecam=True,
                                  interactive=False,
                                  title='SofaVedo',
                                  axes=4)
            self.__plotter.add_callback('timer', self.__update_thread)
            self.__plotter.timer_callback('create', dt=int(self.__fps * 1e3))
            for client in self.__clients:
                client.send(b'done')
            self.__plotter.interactive()

        self.__exit()

    def __update_thread(self, _):

        for i, client in enumerate(self.__clients):
            msg = client.recv(4)
            # Exit command
            if msg == b'exit':
                self.__exit()
            # Step command
            else:
                step = unpack('i', msg)[0]
                if not self.__offscreen:
                    self.__update_instances(step, i)
                client.send(b'done')

    def __update_instances(self, step, idx):
        """
        Update an Actor instance with updated data.

        :param table_name: Name of the Table (one Table per Actor).
        :param data_dict: Updated data of the Actor.
        """

        # 1. Retrieve visual data and update Actors (one Table per Actor)
        for group in self.__actors.keys():
            for table_name in self.__actors[group].keys():
                if f'_{idx}_' in table_name:

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
                        removed = False
                        if do_remove(actor, object_data):
                            self.__plotter.remove(actor.instance, at=actor.group)
                            removed = True
                        # if actor.type in ['Arrows', 'Markers'] and not self.__offscreen:
                        #     self.__plotter.remove(actor.instance, at=actor.group)
                        actor.update(data=object_data)
                        if removed:
                            self.__plotter.add(actor.instance, at=actor.group)
        self.__plotter.render()

    def __exit(self):

        if self.__socket is not None:
            self.__socket.close()
            self.__socket = None
        if self.__plotter is not None:
            self.__plotter.break_interaction()
            self.__plotter.close()
            self.__plotter = None


def do_remove(actor, data):

    if actor.type == 'Arrows' and ('positions' in data.keys() or 'vectors' in data.keys()):
        return True
    elif actor.type == 'Markers' and (len(data) > 0 or 'positions' in actor._object_data['normal_to']._updated_fields):
        return True
    return False

