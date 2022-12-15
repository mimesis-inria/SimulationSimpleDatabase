from typing import Any, Optional, Dict, List
from numpy import array, ndarray
from threading import Thread
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from struct import pack

from SSD.Core.Storage.Database import Database
from Open3dTable import Open3dTable


class Open3dFactory:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 idx_instance: int = 0):

        # Define the Database
        if database is not None:
            self.__database: Database = database
        elif database_name is not None:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)
        else:
            raise ValueError("Both 'database' and 'database_name' are not defined.")

        # Information about all Tables
        self.__tables: List[Open3dTable] = []
        self.__current_id: int = 0
        self.__idx: int = idx_instance
        self.__step: int = 1

        # ExchangeTable to synchronize Factory and Visualizer
        self.__update: Dict[int, bool] = {}
        self.__visualizer_socket: Optional[socket] = None
        Thread(target=self.__link_to_visualizer).start()

    def __link_to_visualizer(self):

        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('localhost', 20000))
        sock.listen(2)
        clients = []
        temp_client_id = 0
        for _ in range(2):
            client, _ = sock.accept()
            client_name = client.recv(1)
            if client_name == b'L':
                temp_client_id = len(clients)
            clients.append(client)
        for client in clients:
            client.send(b'D')
        clients.pop(temp_client_id).close()
        self.__visualizer_socket = clients[0]

    def close(self):

        self.__visualizer_socket.send(b'exit')
        self.__visualizer_socket.close()

    def get_database(self):
        """
        Get the Database instance.
        """

        return self.__database

    def get_path(self):
        """
        Get the path tot the Database.
        """

        return self.__database.get_path()

    def render(self):
        """
        Render the current state of Actors in the Visualizer.
        """

        # Reset all the update flags
        for i in self.__update.keys():
            self.__update[i] = False

        # Send
        self.__step += 1
        try:
            self.__visualizer_socket.send(bytearray(pack('i', self.__step)))
        except ConnectionResetError:
            quit(print('Rendering window closed, shutting down.'))
        except BrokenPipeError:
            quit(print('Rendering window closed, shutting down.'))

    def __add_object(self,
                     object_type: str,
                     data_dict: Dict[str, Any]):

        # The call to 'locals()' in add_ methods also includes the 'self' key
        del data_dict['self']

        # Define the Table name
        table_name = f'{object_type}_{self.__idx}_{self.__current_id}'
        self.__update[self.__current_id] = False
        self.__current_id += 1

        # Create the Table and register the object
        factory = Open3dTable(db=self.__database,
                              table_name=table_name).create_columns()
        factory.send_data(data_dict=data_dict,
                          update=False)
        self.__tables.append(factory)
        return self.__current_id - 1

    def __update_object(self,
                        object_id: int,
                        data_dict: Dict[str, Any]):

        # The call to 'locals()' in update_ methods also includes the 'self' & 'object_id' keys
        del data_dict['self'], data_dict['object_id']

        # Update object data in the Database
        self.__tables[object_id].send_data(data_dict=data_dict,
                                           update=self.__update[object_id])
        if not self.__update[object_id]:
            self.__update[object_id] = True

    def __check_id(self,
                   object_id: int,
                   object_type: str):

        # Negative indexing
        if object_id < 0:
            object_id += len(self.__tables)

        # Check the object type
        current_type = self.__tables[object_id].table_type
        if object_type != current_type:
            raise ValueError(f"The object with ID={object_id} is type'{current_type}', not '{object_type}'. "
                             f"Use Open3dFactory.update_{current_type.lower()}() instead.")
        return object_id

    ########
    # MESH #
    ########

    def add_mesh(self,
                 positions: ndarray,
                 cells: ndarray,
                 at: int = 0,
                 alpha: float = 1.,
                 c: str = 'green',
                 colormap: str = 'jet',
                 scalar_field: ndarray = array([]),
                 wireframe: bool = False,
                 compute_normals: bool = True,
                 line_width: float = 1.):

        return self.__add_object('Mesh', locals())

    def update_mesh(self,
                    object_id: int,
                    positions: Optional[ndarray] = None,
                    alpha: Optional[float] = None,
                    c: Optional[str] = None,
                    scalar_field: Optional[ndarray] = None,
                    wireframe: Optional[bool] = None):

        object_id = self.__check_id(object_id, 'Mesh')
        return self.__update_object(object_id, locals())
