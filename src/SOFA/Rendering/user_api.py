from typing import Optional, Dict, Tuple, Any
from numpy import array, ndarray, tile
import Sofa

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.user_api import UserAPI as CoreUserAPI
from SSD.SOFA.utils import error_message


class UserAPI(Sofa.Core.Controller, CoreUserAPI):

    def __init__(self,
                 root: Sofa.Core.Node,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 non_storing: bool = False,
                 exit_on_window_close: bool = True,
                 idx_instance: int = 0,
                 *args, **kwargs):
        """
        The UserAPI is a Factory used to easily create and update visual objects in the Visualizer.
        This SOFA version brings additional callbacks to automatically get SOFA objects Data.

        :param root: Root node of the sce graph.
        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database to connect to (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param non_storing: If True, the Database will not be stored.
        :param exit_on_window_close: If True, program will be killed if the Visualizer is closed.
        :param idx_instance: If several Factories must be created, specify the index of the Factory.
        """

        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        CoreUserAPI.__init__(self,
                             database=database,
                             database_dir=database_dir,
                             database_name=database_name,
                             remove_existing=remove_existing,
                             non_storing=non_storing,
                             exit_on_window_close=exit_on_window_close,
                             idx_instance=idx_instance)

        # Add the Factory controller to the scene graph
        self.root: Sofa.Core.Node = root
        self.root.addChild('factory')
        self.root.factory.addObject(self)

        self.__callbacks: Dict[int, Tuple[str, Any]] = {}

    def onAnimateEndEvent(self, _) -> None:
        """
        Event called at the end of a time step.
        """

        # Execute all callbacks
        for object_id, (object_type, object_data) in self.__callbacks.items():

            if object_type == 'Mesh':
                self.update_mesh(object_id=object_id,
                                 positions=self.__get_position_data(position_object=object_data))

            elif object_type == 'Points':
                positions = self.__get_position_data(position_object=object_data[0])
                positions = positions[object_data[1]] if object_data[1] is not None else positions
                self.update_points(object_id=object_id,
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
                self.update_arrows(object_id=object_id,
                                   positions=positions,
                                   vectors=vectors * object_data[5])

            elif object_type == 'Markers':
                self.update_markers(object_id=object_id)

        # Execute rendering
        self.render()

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
        if positions is None:
            error_message(f"The object '{position_object.getName()}' does not contain any position data.")
        elif len(positions) == 0:
            error_message(f"The object '{position_object.getName()}' contains an empty position array.")

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
        if forces is None:
            error_message(f"The object '{force_object.getName()} does not contain any force data.")
        elif len(forces) == 0:
            error_message(f"The object '{force_object.getName()} contains an empty force array.")

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
        if cells is None:
            error_message(f"The object {topology_object.getName()} does not contain any topology data with cell type "
                          f"value '{cell_type}'.")
        elif len(cells) == 0:
            error_message(f"The object {topology_object.getName()} contains an empty topology array with cell type "
                          f"value '{cell_type}'.")

        return cells

    def __get_object(self,
                     object_path: str) -> Sofa.Core.Base:

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

    def add_mesh_callback(self,
                          position_object: str,
                          topology_object: Optional[str] = None,
                          cell_type: str = 'triangles',
                          animated=True,
                          at: int = 0,
                          alpha: float = 1.,
                          c: str = 'green',
                          colormap: str = 'jet',
                          scalar_field: ndarray = array([]),
                          wireframe: bool = False,
                          line_width: float = -1.) -> int:
        """
        Add a new Mesh to the Factory with an update callback at each time step.

        :param position_object: Path to an object containing position and eventually topology Data.
        :param topology_object: Path to an object containing topology Data. If not defined, topology data will be
                                searched in 'position_object'.
        :param cell_type: Type of the cells ('edges', 'triangles', 'quads', 'tetrahedra', 'hexahedra').
        :param animated: If True, the object will be automatically updated at each step.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Mesh opacity.
        :param c: Mesh color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Mesh regarding the colormap.
        :param wireframe: If True, the Mesh will be rendered as wireframe.
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
        idx = self.add_mesh(positions=positions,
                            cells=cells,
                            at=at,
                            alpha=alpha,
                            c=c,
                            colormap=colormap,
                            scalar_field=scalar_field,
                            wireframe=wireframe,
                            line_width=line_width)

        # Register object
        if animated:
            self.__callbacks[idx] = ('Mesh', position_object)
        return idx

    def add_points_callback(self,
                            position_object: str,
                            position_indices: Optional[ndarray] = None,
                            animated=True,
                            at: int = 0,
                            alpha: float = 1.,
                            c: str = 'green',
                            colormap: str = 'jet',
                            scalar_field: ndarray = array([]),
                            point_size: int = 4) -> int:
        """
        Add a new Point Cloud to the Factory with an update callback at each time step.

        :param position_object: Path to an object containing position Data.
        :param position_indices: Indices of the positions to extract. If None, all the positions are used.
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
        idx = self.add_points(positions=positions,
                              at=at,
                              alpha=alpha,
                              c=c,
                              colormap=colormap,
                              scalar_field=scalar_field,
                              point_size=point_size)

        # Register object
        if animated:
            self.__callbacks[idx] = ('Points', (position_object, position_indices))
        return idx

    def add_arrows_callback(self,
                            position_object: str,
                            vector_object: Optional[str] = None,
                            dest_object: Optional[str] = None,
                            start_indices: Optional[ndarray] = None,
                            end_indices: Optional[ndarray] = None,
                            scale: float = 1.,
                            animated: bool = True,
                            at: int = 0,
                            alpha: float = 1.,
                            c: str = 'green',
                            colormap: str = 'jet',
                            scalar_field: ndarray = array([]),
                            res: int = 12) -> int:
        """
        Add new Arrows to the Factory with an update callback at each time step.

        :param position_object: Path to an object containing start position Data.
        :param vector_object: Path to an object containing vector Data. If None, vectors will be computed from
                              'dest_object' end positions.
        :param dest_object: Path to an object containing end position Data.
        :param start_indices: Indices of the start positions to extract.
        :param end_indices: Indices of the vectors or the end positions to extract.
        :param scale: Scale factor to apply to vectors.
        :param animated: If True, the object will be automatically updated at each step.
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Arrows opacity.
        :param c: Arrows color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Arrows regarding the colormap.
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
        idx = self.add_arrows(positions=positions,
                              vectors=vectors * scale,
                              at=at,
                              alpha=alpha,
                              c=c,
                              colormap=colormap,
                              scalar_field=scalar_field,
                              res=res)

        # Register object
        if animated:
            if vector_object is not None:
                self.__callbacks[idx] = ('Arrows', ('vec', position_object, start_indices, vector_object,
                                                    end_indices, scale))
            else:
                self.__callbacks[idx] = ('Arrows', ('dst', position_object, start_indices, dest_object,
                                                    end_indices, scale))
        return idx

    def add_markers_callback(self,
                             normal_to: int,
                             indices: ndarray,
                             animated: bool = True,
                             at: int = 0,
                             alpha: float = 1.,
                             c: str = 'green',
                             colormap: str = 'jet',
                             scalar_field: ndarray = array([]),
                             symbol: str = 'o',
                             size: float = 1.,
                             filled: bool = True) -> int:
        """
        Add new Markers to the Factory with an update callback at each time step.

        :param normal_to: Index of the object that defines normals of the Markers.
        :param indices: Indices of the DOFs of the object where the Markers will be centered.
        :param animated:
        :param at: Index of the window in which to Mesh will be rendered.
        :param alpha: Markers opacity.
        :param c: Markers color.
        :param colormap: Colormap scheme name.
        :param scalar_field: Scalar values used to color the Markers regarding the colormap.
        :param symbol: Symbol of a Marker.
        :param size: Size of a Marker.
        :param filled: If True, the symbol is filled.
        """

        # Add object
        idx = self.add_markers(normal_to=normal_to,
                               indices=indices,
                               at=at,
                               alpha=alpha,
                               c=c,
                               colormap=colormap,
                               scalar_field=scalar_field,
                               symbol=symbol,
                               size=size,
                               filled=filled)
        # Register object
        if animated:
            self.__callbacks[idx] = ('Markers', None)
        return idx
