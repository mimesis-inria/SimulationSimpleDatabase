from typing import Dict, Any, List, Optional
from numpy import array, ndarray

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.VedoTable import VedoTable


class VedoFactory:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 idx_instance: int = 0):
        """
        A Factory to manage objects to render and save in the Database.
        User interface to create and update Vedo objects.

        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database to connect to (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param idx_instance: If several Factories must be created, specify the index of the Factory.
        """

        # Define Database
        if database is not None:
            self.__database: Database = database
        elif database_name is not None:
            self.__database: Database = Database(database_dir=database_dir,
                                                 database_name=database_name).new(remove_existing=remove_existing)
        else:
            raise ValueError("Both 'database' and 'database_name' are not defined.")

        # Information about all Tables
        self.__tables: List[VedoTable] = []
        self.__current_id: int = 0
        self.__idx: int = idx_instance

        # ExchangeTable to synchronize Factory and Visualizer
        self.__database.register_pre_save_signal(table_name='Sync',
                                                 handler=self.__sync_visualizer,
                                                 name=f'Factory_{self.__idx}')
        self.__update: Dict[int, bool] = {}

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

    def render(self):
        """
        Render the current state of Actors in the Plotter.
        """

        self.__database.add_data(table_name='Sync',
                                 data={'step': 'F'})

    def __sync_visualizer(self, table_name, data_dict):

        # Reset al the update flags
        for i in self.__update.keys():
            self.__update[i] = False

    def __add_object(self,
                     object_type: str,
                     data_dict: Dict[str, Any]):

        # The call to 'locals()' in add_ methods also includes the 'self' key
        del data_dict['self']

        # Define Table name
        table_name = object_type + f'_{self.__idx}' + f'_{self.__current_id}'
        self.__update[self.__current_id] = False
        self.__current_id += 1

        # Create Table and register object
        factory = VedoTable(db=self.__database,
                            table_name=table_name).create_columns()
        factory.send_data(data_dict=data_dict, update=False)
        self.__tables.append(factory)
        return self.__current_id - 1

    def __update_object(self,
                        object_id: int,
                        data_dict: Dict[str, Any]):

        # The call to 'locals()' in update_ methods also includes the 'self' & 'object_id' keys
        del data_dict['self'], data_dict['object_id']

        # Update object data in Database
        self.__tables[object_id].send_data(data_dict=data_dict, update=self.__update[object_id])
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
            raise ValueError(f"The object with ID={object_id} is type '{current_type}', not '{object_type}'. "
                             f"Use VedoFactory.update_{current_type.lower()}() instead.")
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
                 line_width: float = 0.):
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
        :param compute_normals: If True, the normals of the Mesh are pre-computed.
        :param line_width: Width of the edges of the faces.
        """

        return self.__add_object('Mesh', locals())

    def update_mesh(self,
                    object_id: int,
                    positions: Optional[ndarray] = None,
                    alpha: Optional[float] = None,
                    c: Optional[str] = None,
                    scalar_field: Optional[ndarray] = None,
                    wireframe: Optional[bool] = None):
        """
        Update an existing Mesh in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param positions: Positions of the Mesh DOFs.
        :param alpha: Mesh opacity.
        :param c: Mesh color.
        :param scalar_field: Scalar values used to color the Mesh regarding the colormap.
        :param wireframe: If True, the Mesh will be rendered as wireframe.
        """

        object_id = self.__check_id(object_id, 'Mesh')
        return self.__update_object(object_id, locals())

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
                   point_size: int = 4):
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
                      point_size: Optional[int] = None):
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
        return self.__update_object(object_id, locals())

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
                   res: int = 12):
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

        # TODO: study colormap / scalar_field use
        return self.__add_object('Arrows', locals())

    def update_arrows(self,
                      object_id: int,
                      positions: Optional[ndarray] = None,
                      vectors: Optional[ndarray] = None,
                      alpha: Optional[float] = None,
                      c: Optional[str] = None,
                      scalar_field: Optional[ndarray] = None,
                      res: Optional[int] = None):
        """
        Update existing Arrows in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param positions: Positions of the Arrows DOFs.
        :param vectors: Vectors of the Arrows.
        :param alpha: Arrows opacity.
        :param c: Arrows color.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param res: Circular resolution of the arrows.
        """

        # TODO: study scalar_field use
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
                    size: float = 0.1,
                    filled: bool = True):
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

        normal_to = array([self.__idx, normal_to])
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
                       filled: Optional[bool] = None):
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

        normal_to = array([self.__idx, normal_to]) if normal_to is not None else None
        object_id = self.__check_id(object_id, 'Markers')
        return self.__update_object(object_id, locals())

    ###########
    # SYMBOLS #
    ###########

    def add_symbols(self,
                    positions: ndarray,
                    orientations: ndarray = array([1, 0, 0]),
                    at: int = 0,
                    alpha: float = 1.,
                    c: str = 'green',
                    colormap: str = 'jet',
                    scalar_field: ndarray = array([]),
                    symbol: str = 'o',
                    size: float = 0.1,
                    filled: bool = True):
        """
        Add new symbols to the Factory.

        :param positions: Positions of the Symbols DOFs.
        :param orientations: Orientations of the Symbols. Can be either one orientation for all Symbols either an
                             orientation per Symbol.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Markers opacity.
        :param c: Markers color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param symbol: Symbol of a Marker.
        :param size: Size of a Symbol.
        :param filled: If True, the symbol is filled.
        """
        return self.__add_object('Symbols', locals())

    def update_symbols(self,
                       object_id: int,
                       positions: Optional[ndarray] = None,
                       orientations: Optional[ndarray] = None,
                       alpha: Optional[float] = None,
                       c: Optional[str] = None,
                       scalar_field: Optional[ndarray] = None,
                       symbol: Optional[str] = None,
                       size: Optional[float] = None,
                       filled: Optional[bool] = None):
        """
        Update existing Symbols in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param positions: Positions of the Symbols DOFs.
        :param orientations: Orientations of the Symbols. Can be either one orientation for all Symbols either an
                             orientation per Symbol.
        :param alpha: Markers opacity.
        :param c: Markers color.
        :param scalar_field: Scalar values used to color the Point Cloud regarding the colormap.
        :param symbol: Symbol of a Marker.
        :param size: Size of a Symbol.
        :param filled: If True, the symbol is filled.
        """

        object_id = self.__check_id(object_id, 'Symbols')
        return self.__update_object(object_id, locals())
