from typing import Dict, Any, List, Optional, Tuple
from numpy import array, ndarray
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from struct import pack

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.Visualizer import Visualizer
from SSD.Core.Rendering.backend.DataTables import DataTables


class UserAPI:

    def __init__(self,
                 backend: str = 'vedo',
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 idx_instance: int = 0):
        """
        The UserAPI is a Factory used to easily create and update visual objects in the Visualizer.

        :param backend: The name of the Visualizer to use (either 'vedo' or 'open3d').
        :param database: Database to connect to.
        :param database_dir: Directory that contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database file (used if 'database' is not defined).
        :param remove_existing: If True, overwrite any existing Database file with the same path.
        :param idx_instance: If several Factories are connected to the same Visualizer, specify the index of instances.
        """

        # Check backend
        if backend.lower() not in (available := ['vedo', 'open3d']):
            raise ValueError(f"The backend '{backend}' is not available. Must be in {available}")
        self.__backend = backend.lower()

        # Define the Database
        if database is not None:
            self.__database: Database = database
        elif database_name is not None:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)
        else:
            raise ValueError("Both 'database' and 'database_name' are not defined.")

        # Information about all Tables
        self.__tables: List[DataTables] = []
        self.__current_id: int = 0
        self.__idx: int = idx_instance
        self.__step: int = 1

        # Synchronization between the Factory and the Visualizer
        self.__update: Dict[int, bool] = {}
        self.__socket: Optional[socket] = None

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

    def launch_visualizer(self,
                          offscreen: bool = False,
                          fps: int = 20) -> None:
        """
        Launch the Visualizer.

        :param offscreen: If True, the visualization is done offscreen.
        :param fps: Max frame rate.
        """

        # Launch the Visualizer
        database_path = self.get_database_path()
        Visualizer.launch(backend=self.__backend,
                          database_dir=database_path[0],
                          database_name=database_path[1],
                          offscreen=offscreen,
                          fps=fps)
        # Connect the Factory to the Visualizer
        self.connect_visualizer()

    def connect_visualizer(self):
        """
        Connect the Factory to an existing Visualizer.
        """

        # Connect the Factory to the Visualizer
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Connection attempts while the server is not running on the Visualizer side
        connected = False
        while not connected:
            try:
                self.__socket.connect(('localhost', 20000))
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
            self.__update[i] = False

        # Send the index of the step to render
        self.__step += 1
        try:
            self.__socket.send(bytearray(pack('i', self.__step)))
            # Server is ready
            self.__socket.recv(4)
        except ConnectionResetError:
            quit(print('Rendering window closed, shutting down.'))
        except BrokenPipeError:
            quit(print('Rendering window closed, shutting down.'))

    def close(self):
        """
        Close the Visualization.
        """

        self.__socket.send(b'exit')
        self.__socket.close()

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
        self.__update[self.__current_id] = False
        self.__current_id += 1

        # Create the Table and register the object
        table = DataTables(database=self.__database, table_name=table_name).create_columns()
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

        # Different default values
        if line_width == -1.:
            line_width = 0. if self.__backend == 'vedo' else 1.

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

        # Different default values
        if size == -1:
            size = 1 if self.__backend == 'vedo' else 10
        if font == '':
            font = 'Arial' if self.__backend == 'vedo' else 'monospace'

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
