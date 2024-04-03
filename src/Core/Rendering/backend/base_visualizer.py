from typing import Optional, Tuple, Dict, List
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from struct import unpack

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.backend.base_object import BaseObject


class BaseVisualizer:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 fps: int = 20):
        """
        The BaseVisualizer is the common API for all backend Visualizers.

        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param fps: Max frame rate.
        """

        # Define the Database
        if database is None and database_name is None:
            raise ValueError("Both 'database' and 'database_name' are not defined.")
        if database is not None:
            self.database: Database = database
        else:
            self.database: Database = Database(database_dir=database_dir,
                                               database_name=database_name).new(remove_existing=remove_existing)

        # Visualization parameters
        self.fps: float = 1 / min(max(1, abs(fps)), 50)

        # Objects parameters
        self.objects: Dict[int, Dict[str, BaseObject]] = {}
        self.groups: Dict[str, int] = {}
        self.factories: Dict[int, List[str]] = {}

        # Synchronization with the Factories
        self.server: Optional[socket] = None
        self.clients: List[socket] = []
        self.is_done: List[bool] = []
        self.requests: List[Tuple[int, int]] = []

    @property
    def database_path(self) -> Tuple[str, str]:
        return self.database.get_path()

    def get_object(self,
                   object_name: str) -> BaseObject:
        """
        Get an Object instance.

        :param object_name: Name of the Object.
        """

        group = self.groups[object_name]
        return self.objects[group][object_name]

    def start_visualizer(self,
                         nb_clients: int) -> None:
        """
        Start the Visualizer: create all Objects and render them.

        :param nb_clients: Number of Factories to connect to.
        """

        self.launch_server(nb_clients=nb_clients)
        self.create_objects()
        self.launch_visualizer(nb_clients=nb_clients)

    def launch_server(self,
                      nb_clients: int) -> None:
        """
        Launch the Server and connect to all Factories.

        :param nb_clients: Number of Factories to connect to.
        """

        # Create server
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server.bind(('localhost', 20000))
        self.server.listen()

        # Connect to Factories
        clients = {}
        for _ in range(nb_clients):
            client, _ = self.server.accept()
            # client.settimeout(0.1)
            idx_client: int = unpack('i', client.recv(4))[0]
            clients[idx_client] = client

        # Sort Clients by index
        for idx_client in sorted(clients.keys()):
            self.clients.append(clients[idx_client])
            self.is_done.append(False)

    def create_objects(self) -> None:
        """
        Create an Object for each table in the Database.
        """

        # 1. Sort the Table names per factory index and per object index
        table_names = self.database.get_tables(only_names=True)
        sorted_table_names = []
        sorter: Dict[int, Dict[int, str]] = {}
        for table_name in table_names:
            if len(table_name_split := table_name.split('_')) == 3:
                factory_id, table_id = table_name_split[-2:]
                if int(factory_id) not in sorter:
                    sorter[int(factory_id)] = {}
                sorter[int(factory_id)][int(table_id)] = table_name
        for factory_id in sorted(sorter.keys()):
            for table_id in sorted(sorter[factory_id].keys()):
                sorted_table_names.append(sorter[factory_id][table_id])

        # 2. Retrieve visual data and create Objects (one Table per Object)
        pre_groups = {}
        for table_name in sorted_table_names:

            # 2.1. Get the full line of data
            object_data = self.database.get_line(table_name=table_name)
            object_data.pop('id')
            group = object_data.pop('at')

            # 2.2. Retrieve the good indexing of Objects
            object_type, factory_id = table_name.split('_')[0:2]
            if group not in self.objects:
                self.objects[group] = {}
                pre_groups[group] = []
            if (factory_id := int(factory_id)) not in self.factories:
                self.factories[factory_id] = []
            self.factories[factory_id].append(table_name)

            # 2.3. Create the Object
            self.create_object_backend(object_name=table_name,
                                       object_type=object_type,
                                       object_group=group)
            if object_type == 'Markers':
                object_data['normal_to'] = self.get_object(object_data['normal_to'])
            self.objects[group][table_name].create(data=object_data)
            self.groups[table_name] = group
            pre_groups[group].append(table_name)

        # 3. Update the group values
        for i, group in enumerate(sorted(self.objects.keys())):

            # 3.1. Update value in the Database
            if i != group:
                for table_name in pre_groups[group]:
                    self.database.update(table_name=table_name,
                                         data={'at': i})
            # 3.2. Update value in the Objects
            self.objects[i] = self.objects.pop(group)
            for idx, v_object in self.objects[i].items():
                v_object.group = i
                self.groups[idx] = i

    def create_object_backend(self,
                              object_name: str,
                              object_type: str,
                              object_group: int) -> None:
        """
        Specific Object creation instructions.

        :param object_name: Name of the Object.
        :param object_type: Type of the Object.
        :param object_group: Group of the Object.
        """

        raise NotImplementedError

    def launch_visualizer(self,
                          nb_clients: int) -> None:
        """
        Start the Visualizer: create all Objects and render them.

        :param nb_clients: Number of Factories to connect to.
        """

        raise NotImplementedError

    def listen_client(self,
                      idx_client: int) -> None:
        """
        Communicate with a specific client to add requests to the queue.

        :param idx_client: Index of the Factory.
        """

        while not self.is_done[idx_client]:
            try:
                msg = self.clients[idx_client].recv(4)
                if len(msg) == 0:
                    pass
                elif msg == b'exit':
                    self.is_done[idx_client] = True
                    self.exit(force_quit=False)
                else:
                    step = unpack('i', msg)[0]
                    self.requests.append((idx_client, step))
            except socket.timeout:
                pass

    def update_objects(self,
                       step: int,
                       idx_factory: int) -> None:
        """
        Update the Objects of a Factory.

        :param step: Index of the current step.
        :param idx_factory: Index of the Factory to update.
        """

        for table_name in self.factories[idx_factory]:

            # Get the current step line in the Table
            object_data = self.database.get_line(table_name=table_name,
                                                 line_id=step)
            object_data = dict(filter(lambda item: item[1] is not None, object_data.items()))
            object_data.pop('id')

            # Update the Object and its visualization
            if len(object_data.keys()) > 0 or 'Markers' in table_name:
                v_object = self.get_object(table_name)
                # Markers are updated if their associated object was updated
                if v_object.type == 'Markers' and 'normal_to' in object_data.keys():
                    object_data['normal_to'] = self.get_object(object_data['normal_to'])
                # Update
                v_object.update_data(data=object_data)
                self.update_object_backend(v_object=v_object)

    def update_object_backend(self,
                              v_object: BaseObject) -> None:
        """
        Specific Object update instructions.

        :param v_object: Visual Object.
        """

        raise NotImplementedError

    def exit(self,
             force_quit: bool = True) -> None:
        """
        Exit procedure of the Visualizer.

        :param force_quit: True if the Window was manually closed.
        """

        raise NotImplementedError
