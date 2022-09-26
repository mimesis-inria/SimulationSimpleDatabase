from typing import Optional
from numpy import array, ndarray, tile
import Sofa

from SSD.Generic.Storage.Database import Database
from SSD.Generic.Rendering.VedoFactory import VedoFactory as _VedoFactory


class VedoFactory(Sofa.Core.Controller):
    accessor = {'position': lambda o: o.position.value,
                'positions': lambda o: o.positions.value,
                'edges': lambda o: o.egdes.value,
                'triangles': lambda o: o.triangles.value,
                'quads': lambda o: o.quads.value,
                'tetrahedra': lambda o: o.tetrahedra.value,
                'hexahedra': lambda o: o.hexahedra.value,
                'forces': lambda o: o.forces.value}

    def __init__(self,
                 root: Sofa.Core.Node,
                 database: Optional[Database] = None,
                 database_name: Optional[str] = None,
                 remove_existing: Optional[bool] = False,
                 *args, **kwargs):

        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        self.root = root
        self.__factory = _VedoFactory(database, database_name, remove_existing)
        self.__updates = {}

    @classmethod
    def __get_position_data(cls,
                            position_object: Sofa.Core.Base) -> ndarray:

        try:
            positions = cls.accessor['positions'](position_object)
        except:
            try:
                positions = cls.accessor['position'](position_object)
            except:
                positions = None
        if positions is None or len(positions) == 0:
            print("[ERROR] The given 'record_object' does not contain any positions information or contains empty "
                  "positions.")
            quit()
        return positions

    @classmethod
    def __get_force_data(cls,
                         force_object: Sofa.Core.Base) -> ndarray:

        try:
            forces = cls.accessor['forces'](force_object)
        except:
            forces = None
        if forces is None or len(forces) == 0:
            print("[ERROR] The given 'record_object' does not contain any force information or contains empty forces")
            quit()
        return forces

    @classmethod
    def __get_topology_data(cls,
                            topology_object: Sofa.Core.Base,
                            cell_type: str) -> ndarray:

        if cell_type not in cls.accessor.keys():
            print("[ERROR] The 'cell_type' must be in ['edges', 'triangles', 'quads', 'tetrahedra', 'hexahedra'].")
            quit()
        try:
            cells = cls.accessor[cell_type](topology_object)
        except:
            cells = None
        if cells is None or len(cells) == 0:
            print(f"[ERROR] The given 'topology_object' does not contain any topology information or contains empty "
                  f"topology with cell type = {cell_type}.")
            quit()
        return cells

    def onAnimateEndEvent(self, _):

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

    ########
    # MESH #
    ########

    def add_mesh(self,
                 position_object: Sofa.Core.Base,
                 topology_object: Optional[Sofa.Core.Base] = None,
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

        :param position_object:
        :param cell_type:
        :param topology_object:
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
                   position_object: Sofa.Core.Base,
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
                    position_object: Sofa.Core.Base,
                    vector_object: Optional[Sofa.Core.Base] = None,
                    dest_object: Optional[Sofa.Core.Base] = None,
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

        # Get the positions
        positions = self.__get_position_data(position_object=position_object)
        positions = positions[start_indices] if start_indices is not None else positions

        # Get the orientation vector
        if vector_object is None and dest_object is None:
            print("[ERROR] You must specify an object containing vector data to create arrows (either using "
                  "'vector_object' either using 'dest_object' variables).")
            quit()
        if vector_object is not None:
            vectors = self.__get_force_data(vector_object)
        else:
            dest = self.__get_position_data(position_object=dest_object)
            vectors = dest - positions
        vectors = vectors[end_indices] if end_indices is not None else vectors
        if len(vectors) != 1 and len(vectors) != len(positions):
            print("[ERROR] There must be a vector per DOF.")
            quit()

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
