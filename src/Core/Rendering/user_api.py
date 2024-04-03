from typing import Dict, Any, List, Optional, Tuple
from numpy import array, ndarray
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from struct import pack

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.visualizer import Visualizer
from SSD.Core.Rendering.backend.rendering_table import RenderingTable


class UserAPI:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 non_storing: bool = False,
                 exit_on_window_close: bool = True,
                 idx_instance: int = 0):
        """
        The UserAPI is a Factory used to easily create and update visual objects in the Visualizer.

        :param database: Database to connect to.
        :param database_dir: Directory that contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database file (used if 'database' is not defined).
        :param remove_existing: If True, overwrite any existing Database file with the same path.
        :param non_storing: If True, the Database will not be stored.
        :param exit_on_window_close: If True, program will be killed if the Visualizer is closed.
        :param idx_instance: If several Factories are connected to the same Visualizer, specify the index of instances.
        """

        # Define the Database
        if database is not None:
            self.__database: Database = database
        elif database_name is not None:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)
        else:
            raise ValueError("Both 'database' and 'database_name' are not defined.")
        self.__non_storing = non_storing

        # Information about all Tables
        self.__tables: List[RenderingTable] = []
        self.__current_id: int = 0
        self.__idx: int = idx_instance
        self.__step: int = 1

        # Synchronization between the Factory and the Visualizer
        self.__update: Dict[int, bool] = {}
        self.__socket: Optional[socket] = None
        self.__offscreen: bool = False
        self.__exit_on_close: bool = exit_on_window_close

    def get_database(self) -> Database:
        """
        Get the Database instance.
        """

        return self.__database

    def get_database_path(self) -> Tuple[str, str]:
        """
        Get the path to the Database.
        """

        return self.__database.get_path()

    def launch_visualizer(self,
                          backend: str = 'vedo',
                          offscreen: bool = False,
                          fps: int = 20) -> None:
        """
        Launch the Visualizer.

        :param backend: The name of the Visualizer to use (either 'vedo' or 'open3d').
        :param offscreen: If True, the visualization is done offscreen.
        :param fps: Max frame rate.
        """

        # Check backend
        if backend.lower() not in (available := ['vedo', 'open3d']):
            raise ValueError(f"The backend '{backend}' is not available. Must be in {available}")

        self.__offscreen = offscreen
        if not offscreen:
            # Launch the Visualizer
            database_path = self.get_database_path()
            Visualizer.launch(backend=backend,
                              database_dir=database_path[0],
                              database_name=database_path[1],
                              fps=fps)
            # Connect the Factory to the Visualizer
            self.connect_visualizer()

    def connect_visualizer(self,
                           offscreen: bool = False):
        """
        Connect the Factory to an existing Visualizer.

        :param offscreen: If True, the visualization is done offscreen.
        """

        self.__offscreen = offscreen
        if not offscreen:

            # Connect the Factory to the Visualizer
            self.__socket = socket(AF_INET, SOCK_STREAM)
            self.__socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            # Connection attempts while the server is not running on the Visualizer side
            connected = False
            while not connected:
                try:
                    self.__socket.connect(('localhost', 20000))
                    self.__socket.send(bytearray(pack('i', self.__idx)))
                    connected = True
                except ConnectionRefusedError:
                    pass
            # Server is ready
            self.__socket.recv(4)

    def render(self) -> None:
        """
        Render the current state of visual objects.
        """

        # Add empty lines to non-updated objects & reset all the update flags
        for i in self.__update.keys():
            if not self.__update[i]:
                self.__tables[i].send_data(data={}, update=False)
            self.__update[i] = self.__non_storing

        # Send the index of the step to render
        if not self.__offscreen:
            if self.__socket is not None:
                self.__step += 1 if not self.__non_storing else 0
                try:
                    self.__socket.send(bytearray(pack('i', self.__step)))
                    if self.__socket.recv(4) == b'exit':
                        self.__socket.close()
                        self.__socket = None
                except ConnectionResetError:
                    self.__kill()
                except BrokenPipeError:
                    self.__kill()
            else:
                self.__kill()

    def __kill(self):
        """
        Kill the program on Visualizer close.
        """

        if self.__exit_on_close:
            quit(print('Rendering window closed, shutting down.'))
        if self.__socket is not None:
            self.__socket.close()
            self.__socket = None

    def close(self):
        """
        Close the Visualization.
        """

        if self.__socket is not None:
            self.__socket.send(b'exit')
            self.__socket.close()
            self.__socket = None

        if self.__non_storing:
            self.__database.close(erase_file=True)

    # ###########################
    # OBJECTS CREATION & UPDATE #
    #############################

    def __add_object(self,
                     object_type: str,
                     data: Dict[str, Any]) -> int:

        # The call to 'locals()' in add_ methods also includes the 'self' key
        del data['self']

        # Define the Table name
        table_name = f'{object_type}_{self.__idx}_{self.__current_id}'
        self.__update[self.__current_id] = self.__non_storing
        self.__current_id += 1

        # Create the Table and register the object
        table = RenderingTable(database=self.__database, table_name=table_name).create_columns()
        table.send_data(data=data, update=False)
        self.__tables.append(table)
        return self.__current_id - 1

    def __update_object(self,
                        object_id: int,
                        data: Dict[str, Any]) -> None:

        # The call to 'locals()' in update_ methods also includes the 'self' & 'object_id' keys
        del data['self'], data['object_id']

        # Update object data in the Database
        self.__tables[object_id].send_data(data=data, update=self.__update[object_id])
        if not self.__update[object_id]:
            self.__update[object_id] = True

    def __check_id(self,
                   object_id: int,
                   object_type: str) -> int:

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
                 line_width: float = -1.) -> int:
        """
        Add a new Mesh to the Factory.

        :param positions: Positions of the Mesh DOFs.
        :param cells: Faces of the Mesh.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Mesh opacity.
        :param c: Mesh color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Mesh regarding the colormap.
        :param wireframe: If True, the Mesh will be rendered as wireframe.
        :param line_width: Width of the edges of the faces.
        """

        return self.__add_object('Mesh', locals())

    def update_mesh(self,
                    object_id: int,
                    positions: Optional[ndarray] = None,
                    alpha: Optional[float] = None,
                    c: Optional[str] = None,
                    scalar_field: Optional[ndarray] = None,
                    wireframe: Optional[bool] = None,
                    line_width: Optional[float] = None) -> None:
        """
        Update an existing Mesh in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param positions: Positions of the Mesh DOFs.
        :param alpha: Mesh opacity.
        :param c: Mesh color.
        :param scalar_field: Scalar values used to color the Mesh regarding the colormap.
        :param wireframe: If True, the Mesh will be rendered as wireframe.
        :param line_width: Width of the edges of the faces.
        """

        object_id = self.__check_id(object_id, 'Mesh')
        self.__update_object(object_id, locals())

    ###############
    # POINT CLOUD #
    ###############

    def add_points(self,
                   positions: ndarray,
                   at: int = 0,
                   alpha: float = 1.,
                   c: str = 'green',
                   colormap: str = 'jet',
                   scalar_field: ndarray = array([]),
                   point_size: int = 4) -> int:
        """
        Add a new Point Cloud to the Factory.

        :param positions: Positions of the Point Cloud DOFs.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Point Cloud opacity.
        :param c: Point cloud color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param point_size: Size of the points.
        """

        return self.__add_object('Points', locals())

    def update_points(self,
                      object_id: int,
                      positions: Optional[ndarray] = None,
                      alpha: Optional[float] = None,
                      c: Optional[str] = None,
                      scalar_field: Optional[ndarray] = None,
                      point_size: Optional[int] = None) -> None:
        """
        Update an existing Point Cloud in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param positions: Positions of the Point Cloud DOFs.
        :param alpha: Point Cloud opacity.
        :param c: Point Cloud color.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param point_size: Size of the points.
        """

        object_id = self.__check_id(object_id, 'Points')
        self.__update_object(object_id, locals())

    ##########
    # ARROWS #
    ##########

    def add_arrows(self,
                   positions: ndarray,
                   vectors: ndarray,
                   at: int = 0,
                   alpha: float = 1.,
                   c: str = 'green',
                   colormap: str = 'jet',
                   scalar_field: ndarray = array([]),
                   res: int = 12) -> int:
        """
        Add new Arrows to the Factory.

        :param positions: Positions of the Arrows DOFs.
        :param vectors: Vectors of the Arrows.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Arrows opacity.
        :param c: Arrows color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param res: Circular resolution of the arrows.
        """

        return self.__add_object('Arrows', locals())

    def update_arrows(self,
                      object_id: int,
                      positions: Optional[ndarray] = None,
                      vectors: Optional[ndarray] = None,
                      alpha: Optional[float] = None,
                      c: Optional[str] = None,
                      scalar_field: Optional[ndarray] = None):
        """
        Update existing Arrows in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param positions: Positions of the Arrows DOFs.
        :param vectors: Vectors of the Arrows.
        :param alpha: Arrows opacity.
        :param c: Arrows color.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        """

        object_id = self.__check_id(object_id, 'Arrows')
        return self.__update_object(object_id, locals())

    ###########
    # MARKERS #
    ###########

    def add_markers(self,
                    normal_to: int,
                    indices: ndarray,
                    at: int = 0,
                    alpha: float = 1.,
                    c: str = 'green',
                    colormap: str = 'jet',
                    scalar_field: ndarray = array([]),
                    symbol: str = 'o',
                    size: float = 1.,
                    filled: bool = True) -> int:
        """
        Add new Markers to the Factory.

        :param normal_to: Index of the object that defines normals of the Markers.
        :param indices: Indices of the DOFs of the object where the Markers will be centered.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Markers opacity.
        :param c: Markers color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param symbol: Symbol of a Marker.
        :param size: Size of a Marker.
        :param filled: If True, the symbol is filled.
        """

        normal_to = self.__check_normal_to(normal_to)
        return self.__add_object('Markers', locals())

    def update_markers(self,
                       object_id: int,
                       normal_to: Optional[int] = None,
                       indices: Optional[ndarray] = None,
                       alpha: Optional[float] = None,
                       c: Optional[str] = None,
                       scalar_field: Optional[ndarray] = None,
                       symbol: Optional[str] = None,
                       size: Optional[float] = None,
                       filled: Optional[bool] = None) -> None:
        """
        Update existing Markers in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param normal_to: Index of the object that defines normals of the Markers.
        :param indices: Indices of the DOFs of the object where the Markers will be centered.
        :param alpha: Markers opacity.
        :param c: Markers color.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param symbol: Symbol of a Marker.
        :param size: Size of a Marker.
        :param filled: If True, the symbol is filled.
        """

        object_id = self.__check_id(object_id, 'Markers')
        normal_to = self.__check_normal_to(normal_to) if normal_to is not None else None
        self.__update_object(object_id, locals())

    def __check_normal_to(self,
                          normal_to: int) -> str:

        if (table_type := self.__tables[normal_to].table_type) not in ['Mesh', 'Points']:
            raise ValueError(f"A Marker object can only be associated with a Mesh or Points object. "
                             f"The current Marker was associated to object n°{normal_to} with type {table_type}.")
        return f'{table_type}_{self.__idx}_{normal_to}'

    ########
    # TEXT #
    ########

    def add_text(self,
                 content: str,
                 at: int = 0,
                 corner: str = 'BR',
                 c: str = 'black',
                 font: str = '',
                 size: int = -1,
                 bold: bool = False,
                 italic: bool = False):
        """
        Add new 2D Text to the Factory.

        :param content: Content of the Text.
        :param at: Index of the window in which the Text will be rendered.
        :param corner: Horizontal and vertical positions of the Text between T (top), M (middle) and B (bottom) - for
                       instance, 'BR' stands for 'bottom-right'.
        :param c: Text color.
        :param font: Font of the Text.
        :param size: Size of the font.
        :param bold: Apply bold style to the Text.
        :param italic: Apply italic style to the Text.
        """

        return self.__add_object('Text', locals())

    def update_text(self,
                    object_id: int,
                    content: Optional[str] = None,
                    c: Optional[str] = None,
                    bold: Optional[bool] = None,
                    italic: Optional[bool] = None):
        """
        Update existing Text in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param content: Content of the Text.
        :param c: Text color.
        :param bold: Apply bold style to the Text.
        :param italic: Apply italic style to the Text.
        """

        object_id = self.__check_id(object_id, 'Text')
        return self.__update_object(object_id, locals())
