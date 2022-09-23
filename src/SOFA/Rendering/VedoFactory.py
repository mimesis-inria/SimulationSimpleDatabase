from typing import Optional
from numpy import array, ndarray
import Sofa

from SSD.Generic.Storage.Database import Database
from SSD.Generic.Rendering.VedoFactory import VedoFactory as _VedoFactory


class VedoFactory(Sofa.Core.Controller):

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
                            record_object) -> ndarray:

        try:
            positions = record_object.positions.value
        except:
            try:
                positions = record_object.position.value
            except:
                positions = None
        if positions is None or len(positions) == 0:
            print("[ERROR] The given 'record_object' does not contain any positions information or contains empty "
                  "positions.")
            quit()
        return positions

    @classmethod
    def __get_topology_data(cls,
                            topology_object,
                            cell_type) -> ndarray:

        cells = None
        if cell_type == 'edges':
            try:
                cells = topology_object.edges.value
            except:
                pass
        elif cell_type == 'triangles':
            try:
                cells = topology_object.triangles.value
            except:
                pass
        elif cell_type == 'quads':
            try:
                cells = topology_object.quads.value
            except:
                pass
        elif cell_type == 'tetrahedra':
            try:
                cells = topology_object.tetrahedra.value
            except:
                pass
        elif cell_type == 'hexahedra':
            try:
                cells = topology_object.hexahedra.value
            except:
                pass
        else:
            print("[ERROR] The 'cell_type' must be in ['edges', 'triangles', 'quads', 'tetrahedra', 'hexahedra'].")
            quit()
        if cells is None or len(cells) == 0:
            print(cells, cell_type)
            print(topology_object.triangles.value)
            print("[ERROR] The given 'topology_object' does not contain any topology information or contains empty "
                  "topology.")
            quit()
        return cells

    def onAnimateEndEvent(self, _):

        for object_id, (object_type, record_object) in self.__updates.items():
            if object_type == 'Mesh':
                self.__factory.update_mesh(object_id=object_id,
                                           positions=self.__get_position_data(record_object=record_object))
            elif object_type == 'Points':
                self.__factory.update_points(object_id=object_id,
                                             positions=self.__get_position_data(record_object=record_object))

    ########
    # MESH #
    ########

    def add_mesh(self,
                 record_object: Sofa.Core.Base,
                 cell_type: str,
                 topology_object: Optional[Sofa.Core.Base] = None,
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

        :param record_object:
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
        cells = self.__get_topology_data(topology_object=record_object if topology_object is None else topology_object,
                                         cell_type=cell_type)
        # Get the positions
        positions = self.__get_position_data(record_object=record_object)

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
            self.__updates[idx] = ('Mesh', record_object)
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
                   record_object: Sofa.Core.Base,
                   animated=True,
                   at: int = -1,
                   alpha: float = 1.,
                   c: str = 'green',
                   colormap: str = 'jet',
                   scalar_field: ndarray = array([]),
                   point_size: int = 4):
        """
        Add a new Mesh to the Factory.

        :param record_object:
        :param animated: If True, the object will be automatically updated at each step.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Mesh opacity.
        :param c: Mesh color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Mesh regarding the colormap.
        :param point_size: Size of the points.
        """

        # Get the positions
        positions = self.__get_position_data(record_object=record_object)

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
            self.__updates[idx] = ('Points', record_object)
        return idx
