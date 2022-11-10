from typing import Optional, Dict, Tuple, Any
from numpy import array, ndarray, tile
import Sofa

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.VedoFactory import VedoFactory as _VedoFactory
from SSD.SOFA.utils import error_message


class VedoFactory(Sofa.Core.Controller):

    def __init__(self,
                 root: Sofa.Core.Node,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 idx_instance: int = 0,
                 *args, **kwargs):
        """
            A Factory to manage objects to render and save in the Database.
            User interface to create and update Vedo objects.
            Additional callbacks to automatically get SOFA objects Data.

            :param root: Root node of the sce graph.
            :param database: Database to connect to.
            :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
            :param database_name: Name of the Database to connect to (used if 'database' is not defined).
            :param remove_existing: If True, overwrite a Database with the same path.
            :param idx_instance: If several Factories must be created, specify the index of the Factory.
            """

        Sofa.Core.Controller.__init__(self, *args, **kwargs)

        # Add the Factory controller to the scene graph
        self.root: Sofa.Core.Node = root
        self.root.addChild('factory')
        self.root.factory.addObject(self)

        self.__factory: _VedoFactory = _VedoFactory(database=database,
                                                    database_dir=database_dir,
                                                    database_name=database_name,
                                                    remove_existing=remove_existing,
                                                    idx_instance=idx_instance)
        self.__updates: Dict[int, Tuple[str, Any]] = {}

    @classmethod
    def __get_position_data(cls,
                            position_object: Sofa.Core.Base) -> ndarray:

        # Try to access Data field
        if (data := position_object.getData('positions')) is None:
            if (data := position_object.getData('position')) is None:
                positions = None
            else:
                positions = data.value
        else:
            positions = data.value

        # Check value
        if positions is None or len(positions) == 0:
            error_message(f"The object '{position_object.getName()}' does not contain any position data or contains an "
                          f"empty position array.")
        positions = array(positions) if type(positions[0]) != ndarray else positions
        return positions[:, :3]

    @classmethod
    def __get_force_data(cls,
                         force_object: Sofa.Core.Base) -> ndarray:

        # Try to access Data field
        if (data := force_object.getData('forces')) is None:
            if (data := force_object.getData('force')) is None:
                forces = None
            else:
                forces = data.value
        else:
            forces = data.value

        # Check value
        if forces is None or len(forces) == 0:
            error_message(f"The object '{force_object.getName()} does not contain any force data or contains an empty "
                          f"force array.")
        return forces

    @classmethod
    def __get_topology_data(cls,
                            topology_object: Sofa.Core.Base,
                            cell_type: str) -> ndarray:

        # Check cell type
        available_cell_types = ['edges', 'triangles', 'quads', 'tetrahedra', 'hexahedra']
        if cell_type not in available_cell_types:
            error_message(f"Wrong cell type value '{cell_type}'. The cell type must be in {available_cell_types}.")

        # Try to access Data field
        if (data := topology_object.getData(cell_type)) is None:
            cells = None
        else:
            cells = data.value

        # Check value
        if cells is None or len(cells) == 0:
            error_message(f"The object {topology_object.getName()} does not contain any topology data or contains an "
                          f"empty topology array with cell type value '{cell_type}'.")
        return cells

    def onAnimateEndEvent(self, _):
        """
        At the end of a time step.
        """

        # Execute all callbacks
        for object_id, (object_type, object_data) in self.__updates.items():

            if object_type == 'Mesh':
                self.__factory.update_mesh(object_id=object_id,
                                           positions=self.__get_position_data(position_object=object_data))

            elif object_type == 'Points':
                positions = self.__get_position_data(position_object=object_data[0])
                positions = positions[object_data[1]] if object_data[1] is not None else positions
                self.__factory.update_points(object_id=object_id,
                                             positions=positions)

            elif object_type == 'Arrows':
                positions = self.__get_position_data(position_object=object_data[1])
                positions = positions[object_data[2]] if object_data[2] is not None else positions
                if object_data[0] == 'vec':
                    vectors = self.__get_force_data(object_data[3])
                else:
                    vectors = self.__get_position_data(object_data[3]) - positions
                vectors = vectors[object_data[4]] if object_data[4] is not None else vectors
                if len(vectors) == 1:
                    vectors = tile(vectors, (len(positions), 1))
                self.__factory.update_arrows(object_id=object_id,
                                             positions=positions,
                                             vectors=vectors * object_data[5])

            elif object_type == 'Markers':
                self.__factory.update_markers(object_id=object_id)

        # Execute rendering
        self.__factory.render()

    def __get_object(self,
                     object_path: str):

        # Check the path
        if object_path[0] != '@' or len(object_path[1:].split('.')) == 0:
            error_message(f"You must give the absolute path to the object to record. "
                          f"The path '{object_path}' must be defined such as '@child_node.object_name'.")

        # Access each child node
        node: Sofa.Core.Node = self.root
        child_nodes = object_path[1:].split('.')[:-1]
        if len(child_nodes) > 0 and child_nodes[0] == node.getName():
            child_nodes.pop(0)
        for child_node in child_nodes:
            if child_node not in node.children:
                node_path = f'{self.root.getName()}{node.getPathName()}'
                error_message(f"The node '{child_node}' is not a child of '{node_path}'. "
                              f"Available children are {[n.getName() for n in node.children]}.")
            node = node.getChild(child_node)

        # Access object
        object_name = object_path[1:].split('.')[-1]
        if object_name not in node.objects:
            node_path = f'{self.root.getName()}{node.getPathName()}'
            error_message(f"The object '{object_name} does not belong to node '{node_path}'. "
                          f"Available objects are {[o.getName() for o in node.objects]}.")
        return node.getObject(object_name)

    ########
    # MESH #
    ########

    def add_mesh(self,
                 position_object: str,
                 topology_object: Optional[str] = None,
                 cell_type: str = 'triangles',
                 animated=True,
                 at: int = -1,
                 alpha: float = 1.,
                 c: str = 'green',
                 colormap: str = 'jet',
                 scalar_field: ndarray = array([]),
                 wireframe: bool = False,
                 compute_normals: bool = True,
                 line_width: float = 0.):
        """
        Add a new Mesh to the Factory.

        :param position_object: Path to an object containing position and eventually topology Data.
        :param topology_object: Path to an object containing topology Data.
        :param cell_type: Type of the cells ('edges', 'triangles', 'quads', 'tetrahedra', 'hexahedra').
        :param animated: If True, the object will be automatically updated at each step.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Mesh opacity.
        :param c: Mesh color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Mesh regarding the colormap.
        :param wireframe: If True, the Mesh will be rendered as wireframe.
        :param compute_normals: If True, the normals of the Mesh are pre-computed.
        :param line_width: Width of the edges of the faces.
        """

        # Get the objects
        position_object = self.__get_object(object_path=position_object)
        topology_object = position_object if topology_object is None \
            else self.__get_object(object_path=topology_object)

        # Get the cells
        cells = self.__get_topology_data(
            topology_object=position_object if topology_object is None else topology_object,
            cell_type=cell_type)
        # Get the positions
        positions = self.__get_position_data(position_object=position_object)

        # Add object
        idx = self.__factory.add_mesh(positions=positions,
                                      cells=cells,
                                      at=at,
                                      alpha=alpha,
                                      c=c,
                                      colormap=colormap,
                                      scalar_field=scalar_field,
                                      wireframe=wireframe,
                                      compute_normals=compute_normals,
                                      line_width=line_width)

        # Register object
        if animated:
            self.__updates[idx] = ('Mesh', position_object)
        return idx

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

        self.__factory.update_mesh(object_id=object_id,
                                   positions=positions,
                                   alpha=alpha,
                                   c=c,
                                   scalar_field=scalar_field,
                                   wireframe=wireframe)

    ##########
    # POINTS #
    ##########

    def add_points(self,
                   position_object: str,
                   position_indices: Optional[ndarray] = None,
                   animated=True,
                   at: int = -1,
                   alpha: float = 1.,
                   c: str = 'green',
                   colormap: str = 'jet',
                   scalar_field: ndarray = array([]),
                   point_size: int = 4):
        """
        Add a new Mesh to the Factory.

        :param position_object:
        :param position_indices:
        :param animated: If True, the object will be automatically updated at each step.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Mesh opacity.
        :param c: Mesh color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Mesh regarding the colormap.
        :param point_size: Size of the points.
        """

        # Get the object
        position_object = self.__get_object(object_path=position_object)

        # Get the positions
        positions = self.__get_position_data(position_object=position_object)
        positions = positions[position_indices] if position_indices is not None else positions

        # Add object
        idx = self.__factory.add_points(positions=positions,
                                        at=at,
                                        alpha=alpha,
                                        c=c,
                                        colormap=colormap,
                                        scalar_field=scalar_field,
                                        point_size=point_size)

        # Register object
        if animated:
            self.__updates[idx] = ('Points', (position_object, position_indices))
        return idx

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

        self.__factory.update_points(object_id=object_id,
                                     positions=positions,
                                     alpha=alpha,
                                     c=c,
                                     scalar_field=scalar_field,
                                     point_size=point_size)

    ###########
    # VECTORS #
    ###########

    def add_vectors(self,
                    position_object: str,
                    vector_object: Optional[str] = None,
                    dest_object: Optional[str] = None,
                    start_indices: Optional[ndarray] = None,
                    end_indices: Optional[ndarray] = None,
                    scale: float = 1.,
                    animated: bool = True,
                    at: int = -1,
                    alpha: float = 1.,
                    c: str = 'green',
                    res: int = 12):
        """
        Add new Arrows to the Factory.

        :param position_object:
        :param vector_object:
        :param dest_object:
        :param start_indices:
        :param end_indices:
        :param scale:
        :param animated:
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Arrows opacity.
        :param c: Arrows color.
        :param res: Circular resolution of the arrows.
        """

        # Get the objects
        position_object = self.__get_object(object_path=position_object)
        vector_object = self.__get_object(object_path=vector_object) if vector_object is not None else None
        dest_object = self.__get_object(object_path=dest_object) if dest_object is not None else None

        # Get the positions
        positions = self.__get_position_data(position_object=position_object)
        positions = positions[start_indices] if start_indices is not None else positions

        # Get the orientation vector
        if vector_object is None and dest_object is None:
            error_message("You must specify an object containing vector data to create arrows (either using "
                          "'vector_object' either using 'dest_object' variables).")
        if vector_object is not None:
            vectors = self.__get_force_data(vector_object)
        else:
            dest = self.__get_position_data(position_object=dest_object)
            vectors = dest - positions
        vectors = vectors[end_indices] if end_indices is not None else vectors
        if len(vectors) != 1 and len(vectors) != len(positions):
            error_message("There must be a vector per DOF.")

        if len(vectors) == 1:
            vectors = tile(vectors, (len(positions), 1))

        # Add object
        idx = self.__factory.add_arrows(positions=positions,
                                        vectors=vectors * scale,
                                        at=at,
                                        alpha=alpha,
                                        c=c,
                                        res=res)

        # Register object
        if animated:
            if vector_object is not None:
                self.__updates[idx] = ('Arrows', ('vec', position_object, start_indices, vector_object,
                                                  end_indices, scale))
            else:
                self.__updates[idx] = ('Arrows', ('dst', position_object, start_indices, dest_object,
                                                  end_indices, scale))
        return idx

    def update_arrows(self,
                      object_id: int,
                      positions: Optional[ndarray] = None,
                      vectors: Optional[ndarray] = None,
                      alpha: Optional[float] = None,
                      c: Optional[str] = None,
                      res: Optional[int] = None):
        """
        Update existing Arrows in the Factory.

        :param object_id: Index of the object (follows the global order of creation).
        :param positions: Positions of the Arrows DOFs.
        :param vectors: Vectors of the Arrows.
        :param alpha: Arrows opacity.
        :param c: Arrows color.
        :param res: Circular resolution of the arrows.
        """

        self.__factory.update_arrows(object_id=object_id,
                                     positions=positions,
                                     vectors=vectors,
                                     alpha=alpha,
                                     c=c,
                                     res=res)

    ###########
    # MARKERS #
    ###########

    def add_markers(self,
                    normal_to: int,
                    indices: ndarray,
                    animated: bool = True,
                    at: int = -1,
                    alpha: float = 1.,
                    c: str = 'green',
                    symbol: str = 'o',
                    size: float = 0.1,
                    filled: bool = True):
        """
        Add new Markers to the Factory.

        :param normal_to: Index of the object that defines normals of the Markers.
        :param indices: Indices of the DOFs of the object where the Markers will be centered.
        :param animated:
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Markers opacity.
        :param c: Markers color.
        :param symbol: Symbol of a Marker.
        :param size: Size of a Marker.
        :param filled: If True, the symbol is filled.
        """

        # Add object
        idx = self.__factory.add_markers(normal_to=normal_to,
                                         indices=indices,
                                         at=at,
                                         alpha=alpha,
                                         c=c,
                                         symbol=symbol,
                                         size=size,
                                         filled=filled)
        # Register object
        if animated:
            self.__updates[idx] = ('Markers', None)
        return idx

    def update_markers(self,
                       object_id: int,
                       normal_to: Optional[int] = None,
                       indices: Optional[ndarray] = None,
                       alpha: Optional[float] = None,
                       c: Optional[str] = None,
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
        :param symbol: Symbol of a Marker.
        :param size: Size of a Marker.
        :param filled: If True, the symbol is filled.
        """

        self.__factory.update_markers(object_id=object_id,
                                      normal_to=normal_to,
                                      indices=indices,
                                      alpha=alpha,
                                      c=c,
                                      symbol=symbol,
                                      size=size,
                                      filled=filled)
