from typing import Any, Optional, Dict, List
import open3d as o3d
from vedo.colors import get_color
from numpy import array, ndarray, asarray, sort, concatenate, unique, tile, eye, arctan, cos, sin
from numpy.linalg import norm
from matplotlib.colors import Normalize
from matplotlib.pyplot import get_cmap


class Open3dActor:

    def __init__(self,
                 actor_type: str,
                 actor_name: str,
                 actor_group: int):
        """

        :param actor_type:
        :param actor_name:
        :param actor_group:
        """

        # Actor information
        self.type: str = actor_type
        self.name: str = actor_name
        self.group: str = str(actor_group)
        self.instance: Optional[o3d.geometry.Geometry3D] = None
        self.material = o3d.visualization.rendering.MaterialRecord()

        # Actor data
        self.__object_data: Optional[Dict[str, Any]] = None
        self.__cmap_data: Optional[Dict[str, Any]] = None

        # Actor specialization methods
        spec = {'Mesh': (self.__create_mesh, self.__update_mesh, self.__cmap_mesh),
                'Points': (self.__create_points, self.__update_points, self.__cmap_points),
                'Arrows': (self.__create_arrows, self.__update_arrows, self.__cmap_arrows)}
        self.__create_object = spec[self.type][0]
        self.__update_object = spec[self.type][1]
        self.__cmap_object = spec[self.type][2]

    def create(self,
               object_data: Dict[str, Any]):
        """

        :param object_data:
        """

        # Sort data
        cmap_data = {}
        for field in ['colormap', 'scalar_field']:
            if field in object_data:
                cmap_data[field] = object_data.pop(field)
        # Register Actor data
        self.__object_data = object_data
        self.__cmap_data = cmap_data
        # Create the object
        self.__create_object(self.__object_data)
        # Apply the colormap
        if len(cmap_data.keys()) > 1:
            self.apply_cmap(self.__cmap_data)

    def update(self,
               object_data: Dict[str, Any]):
        """

        :param object_data:
        """

        # Sort data
        cmap_data = {'scalar_field': object_data.pop('scalar_field')} if 'scalar_field' in object_data else {}
        # Register Actor data
        updated_object_fields = []
        for key, value in object_data.items():
            self.__object_data[key] = value
            updated_object_fields.append(key)
        for key, value in cmap_data.items():
            self.__cmap_data[key] = value
        # Update the object
        if len(object_data.keys()) > 0:
            self.__update_object(self.__object_data, updated_object_fields)
        # Apply the colormap
        if len(cmap_data.keys()) > 0:
            self.apply_cmap(self.__cmap_data)

    def apply_cmap(self,
                   cmap_data: Dict[str, Any]):
        """

        :param cmap_data:
        """

        scalar_field = cmap_data['scalar_field']
        if len(scalar_field) > 0:
            # Normalize scalar field
            cmap_norm = Normalize(vmin=min(scalar_field[0]),
                                  vmax=max(scalar_field[0]))
            cmap = get_cmap(cmap_data['colormap'])
            vertex_colors = cmap(cmap_norm(scalar_field[0]))[:, 0:3]
            # Apply colors
            self.__cmap_object(vertex_colors)

    ########
    # MESH #
    ########

    def __create_mesh(self,
                      data: Dict[str, Any]):

        # Create the material
        alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
        color = list(get_color(rgb=data['c']))
        self.material.base_color = array(color + [alpha])
        self.material.shader = 'unlitLine' if data['wireframe'] else 'defaultLitTransparency'

        # Create instance
        if data['wireframe']:
            self.material.line_width = data['line_width']
            edges = concatenate([sort(data['cells'][:, col], axis=1) for col in [[0, 1], [1, 2], [2, 0]]])
            edges = unique(edges, axis=0)
            self.instance = o3d.geometry.LineSet(points=o3d.utility.Vector3dVector(data['positions']),
                                                 lines=o3d.utility.Vector2iVector(edges))
        else:
            self.instance = o3d.geometry.TriangleMesh(vertices=o3d.utility.Vector3dVector(data['positions']),
                                                      triangles=o3d.utility.Vector3iVector(data['cells']))
            self.instance.compute_vertex_normals()

    def __update_mesh(self,
                      data: Dict[str, Any],
                      updated_fields: List[str]):

        # Check wireframe change
        if 'wireframe' in updated_fields:
            if (data['wireframe'] and self.material.shader == 'defaultLitTransparency') or \
                    (not data['wireframe'] and self.material.shader == 'unlitLine'):
                self.__create_object(self.__object_data)

        # Update the material
        if 'alpha' in updated_fields or 'c' in updated_fields:
            alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
            color = list(get_color(rgb=data['c']))
            self.material.base_color = array(color + [alpha])

        # Update positions
        if 'positions' in updated_fields:
            if self.__object_data['wireframe']:
                self.instance.points = o3d.utility.Vector3dVector(data['positions'])
            else:
                self.instance.vertices = o3d.utility.Vector3dVector(data['positions'])

    def __cmap_mesh(self,
                    vertex_colors: ndarray):

        alpha = 1 if not 0. <= self.__object_data['alpha'] <= 1. else self.__object_data['alpha']

        if self.__object_data['wireframe']:
            line_color = vertex_colors[asarray(self.instance.lines)[:, 0]]
            self.instance.colors = o3d.utility.Vector3dVector(line_color)
            self.material.base_color = array([1., 1., 1., alpha])
        else:
            self.instance.vertex_colors = o3d.utility.Vector3dVector(vertex_colors)
            self.material.base_color = array([1., 1., 1., alpha])

    ###############
    # POINT CLOUD #
    ###############

    def __create_points(self,
                        data: Dict[str, Any]):

        # Create the material
        alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
        color = list(get_color(rgb=data['c']))
        self.material.base_color = array(color + [alpha])
        self.material.shader = 'defaultLitTransparency'
        self.material.point_size = data['point_size']

        # Create instance
        self.instance = o3d.geometry.PointCloud(points=o3d.utility.Vector3dVector(data['positions']))

    def __update_points(self,
                        data: Dict[str, Any],
                        updated_fields: List[str]):

        # Update material
        if 'alpha' in updated_fields or 'c' in updated_fields:
            alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
            color = list(get_color(rgb=data['c']))
            self.material.base_color = array(color + [alpha])
        if 'point_size' in updated_fields:
            self.material.point_size = data['point_size']

        # Update positions
        if 'positions' in updated_fields:
            self.instance.points = o3d.utility.Vector3dVector(data['positions'])

    def __cmap_points(self,
                      vertex_colors: ndarray):

        alpha = 1 if not 0. <= self.__object_data['alpha'] <= 1. else self.__object_data['alpha']
        self.instance.colors = o3d.utility.Vector3dVector(vertex_colors)
        self.material.base_color = array([1., 1., 1., alpha])

    ##########
    # ARROWS #
    ##########

    def __create_arrows(self,
                        data: Dict[str, Any]):

        # Create the material
        alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
        color = list(get_color(rgb=data['c']))
        self.material.base_color = array(color + [alpha])
        self.material.shader = 'defaultLitTransparency'

        # Create instance
        for start, vec in zip(data['positions'], data['vectors']):
            scale = norm(vec)
            arrow = o3d.geometry.TriangleMesh().create_arrow(resolution=data['res'],
                                                             cone_height=scale * 0.3,
                                                             cone_radius=scale / 10,
                                                             cylinder_height=scale * 0.7,
                                                             cylinder_radius=scale / 20)
            T = eye(4)
            T[:3, -1] = start
            gamma = arctan(vec[1] / vec[0])
            Rz = array([[cos(gamma), -sin(gamma), 0],
                        [sin(gamma), cos(gamma), 0],
                        [0, 0, 1]])
            vec = Rz.T @ vec.reshape(-1, 1)
            vec = vec.reshape(-1)
            beta = arctan(vec[0] / vec[2])
            Ry = array([[cos(beta), 0, sin(beta)],
                        [0, 1, 0],
                        [-sin(beta), 0, cos(beta)]])
            arrow.rotate(Ry, center=array([0, 0, 0]))
            arrow.rotate(Rz, center=array([0, 0, 0]))
            arrow.translate(start)
            if self.instance is None:
                self.instance = arrow
            else:
                self.instance += arrow
        self.instance.compute_vertex_normals()

    def __update_arrows(self,
                        data: Dict[str, Any],
                        updated_fields: List[str]):

        pass

    def __cmap_arrows(self,
                      vertex_colors: ndarray):

        nb_arrow = vertex_colors.shape[0]
        nb_dof_arrow = asarray(self.instance.vertices).shape[0] // nb_arrow
        alpha = 1 if not 0. <= self.__object_data['alpha'] <= 1. else self.__object_data['alpha']
        transformed_vertex_color = concatenate(tuple(tile(color, (nb_dof_arrow, 1)) for color in vertex_colors))
        self.instance.vertex_colors = o3d.utility.Vector3dVector(transformed_vertex_color)
        self.material.base_color = array([1., 1., 1., alpha])
