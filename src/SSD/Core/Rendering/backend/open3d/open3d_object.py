from typing import Any, Optional, Dict, List
import open3d as o3d
import open3d.visualization.gui as gui
from vedo import Marker, Glyph
from vedo.colors import get_color
from numpy import array, ndarray, asarray, concatenate, tile
from numpy.linalg import norm
from matplotlib.colors import Normalize
from matplotlib.pyplot import get_cmap

from SSD.Core.Rendering.backend.base_object import BaseObject
from SSD.Core.Rendering.backend.open3d.utils import get_rotation_matrix


class Open3dObject(BaseObject):

    def __init__(self,
                 object_type: str,
                 object_name: str,
                 object_group: int):
        """
        The Open3dObject is used to create and update Open3D object instances.

        :param object_type: Type of the Object.
        :param object_name: Name of the Object.
        :param object_group: Index of the group of the Object.
        """

        BaseObject.__init__(self,
                            object_type=object_type,
                            object_name=object_name,
                            object_group=object_group)

        # Object information
        self.instance: Optional[o3d.geometry.Geometry3D] = None
        self.material = o3d.visualization.rendering.MaterialRecord()
        self.utils: Optional[Any] = None

        # Object specialization
        spec = {'Mesh': (self.__create_mesh, self.__update_mesh, self.__cmap_mesh),
                'Points': (self.__create_points, self.__update_points, self.__cmap_points),
                'Arrows': (self.__create_arrows, self.__update_arrows, self.__cmap_arrows),
                'Markers': (self.__create_markers, self.__update_markers, self.__cmap_markers),
                'Text': (self.__create_text, self.__update_text, self.__cmap_text)}
        self._create_object = spec[self.type][0]
        self._update_object = spec[self.type][1]
        self._cmap_object = spec[self.type][2]

    def apply_cmap(self,
                   data: Dict[str, Any]) -> None:
        """
        General colormap apply method.

        :param data: Colormap data.
        """

        scalar_field = data['scalar_field']
        if len(scalar_field) > 0:
            # Normalize scalar field
            cmap_norm = Normalize(vmin=min(scalar_field[0]),
                                  vmax=max(scalar_field[0]))
            # Get the colormap
            cmap = get_cmap(data['colormap'])
            # Create color vector
            vertex_colors = cmap(cmap_norm(scalar_field[0]))[:, 0:3]
            # Apply colors
            self._cmap_object(vertex_colors)

    ########
    # MESH #
    ########

    def __create_mesh(self,
                      data: Dict[str, Any]) -> None:

        # Create the material
        alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
        color = list(get_color(rgb=data['c']))
        self.material.base_color = array(color + [alpha])
        self.material.shader = 'unlitLine' if data['wireframe'] else 'defaultLitTransparency'

        # Create instance
        if data['wireframe']:
            data['line_width'] = 1. if data['line_width'] == -1. else data['line_width']
            self.material.line_width = data['line_width']
            self.utils = o3d.geometry.TriangleMesh(vertices=o3d.utility.Vector3dVector(data['positions']),
                                                   triangles=o3d.utility.Vector3iVector(data['cells']))
            self.utils.compute_vertex_normals()
            self.instance = o3d.geometry.LineSet().create_from_triangle_mesh(self.utils)
        else:
            self.instance = o3d.geometry.TriangleMesh(vertices=o3d.utility.Vector3dVector(data['positions']),
                                                      triangles=o3d.utility.Vector3iVector(data['cells']))
            self.instance.compute_vertex_normals()

    def __update_mesh(self,
                      data: Dict[str, Any],
                      updated_fields: List[str]) -> None:

        # Check wireframe change
        if 'wireframe' in updated_fields:
            if (data['wireframe'] and self.material.shader == 'defaultLitTransparency') or \
                    (not data['wireframe'] and self.material.shader == 'unlitLine'):
                self._create_object(data)

        # Update the material
        if 'alpha' in updated_fields or 'c' in updated_fields:
            alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
            color = list(get_color(rgb=data['c']))
            self.material.base_color = array(color + [alpha])

        # Update positions
        if 'positions' in updated_fields:
            if self._object_data['wireframe']:
                self.utils.vertices = o3d.utility.Vector3dVector(data['positions'])
                self.instance.points = o3d.utility.Vector3dVector(data['positions'])
                self.utils.compute_vertex_normals()
            else:
                self.instance.vertices = o3d.utility.Vector3dVector(data['positions'])
                self.instance.compute_vertex_normals()

    def __cmap_mesh(self,
                    vertex_colors: ndarray) -> None:

        alpha = 1 if not 0. <= self._object_data['alpha'] <= 1. else self._object_data['alpha']
        if self._object_data['wireframe']:
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
                        data: Dict[str, Any]) -> None:

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
                        updated_fields: List[str]) -> None:

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
                      vertex_colors: ndarray) -> None:

        alpha = 1 if not 0. <= self._object_data['alpha'] <= 1. else self._object_data['alpha']
        self.instance.colors = o3d.utility.Vector3dVector(vertex_colors)
        self.material.base_color = array([1., 1., 1., alpha])

    ##########
    # ARROWS #
    ##########

    def __create_arrows(self,
                        data: Dict[str, Any]) -> None:

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
                                                             cone_radius=scale * 0.1,
                                                             cylinder_height=scale * 0.7,
                                                             cylinder_radius=scale * 0.05)
            R = get_rotation_matrix(vec)
            arrow.rotate(R, center=array([0., 0., 0.]))
            arrow.translate(start)
            if self.instance is None:
                self.instance = arrow
            else:
                self.instance += arrow
        self.instance.compute_vertex_normals()

    def __update_arrows(self,
                        data: Dict[str, Any],
                        updated_fields: List[str]) -> None:

        # Update vectors
        if 'positions' in updated_fields or 'vectors' in updated_fields:
            self.instance = None
            self._create_object(data)

        # Update material
        elif 'alpha' in updated_fields or 'c' in updated_fields:
            alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
            color = list(get_color(rgb=data['c']))
            self.material.base_color = array(color + [alpha])

    def __cmap_arrows(self,
                      vertex_colors: ndarray) -> None:

        nb_arrow = vertex_colors.shape[0]
        nb_dof_arrow = asarray(self.instance.vertices).shape[0] // nb_arrow
        alpha = 1 if not 0. <= self._object_data['alpha'] <= 1. else self._object_data['alpha']
        transformed_vertex_color = concatenate(tuple(tile(color, (nb_dof_arrow, 1)) for color in vertex_colors))
        self.instance.vertex_colors = o3d.utility.Vector3dVector(transformed_vertex_color)
        self.material.base_color = array([1., 1., 1., alpha])

    ###########
    # MARKERS #
    ###########

    def __create_markers(self,
                         data: Dict[str, Any]) -> None:

        # Create the material
        alpha = 1 if not 0. <= data['alpha'] <= 1. else data['alpha']
        color = list(get_color(rgb=data['c']))
        self.material.base_color = array(color + [alpha])
        self.material.shader = 'defaultLitTransparency'
        self.material.shader = 'defaultLitTransparency' if data['filled'] else 'unlitLine'

        # Get position and orientation information
        normal_to = data['normal_to']
        if normal_to.type == 'Mesh':
            if normal_to.material.shader == 'defaultLitTransparency':
                positions = asarray(normal_to.instance.vertices)[data['indices']][0]
                orientations = asarray(normal_to.instance.vertex_normals)[data['indices']][0]
            else:
                positions = asarray(normal_to.utils.vertices)[data['indices']][0]
                orientations = asarray(normal_to.utils.vertex_normals)[data['indices']][0]
        elif normal_to.type == 'Points':
            positions = asarray(normal_to.instance.points)[data['indices']][0]
            orientations = asarray(normal_to.instance.normals)[data['indices']][0]
        else:
            raise ValueError

        # Create the Marker mesh
        vedo_marker = Marker(symbol=data['symbol'],
                             s=data['size']).rotate(axis=[0, 1, 0], angle=90, rad=False)
        vedo_glyph = Glyph(mesh=positions,
                           glyph=vedo_marker,
                           orientation_array=orientations).triangulate()
        self.instance = o3d.geometry.TriangleMesh(vertices=o3d.utility.Vector3dVector(vedo_glyph.vertices),
                                                  triangles=o3d.utility.Vector3iVector(array(vedo_glyph.cells)))
        self.instance.compute_vertex_normals()

    def __update_markers(self,
                         data: Dict[str, Any],
                         updated_fields: List[str]) -> None:

        if len(updated_fields) > 0 or 'positions' in data['normal_to'].updated_fields:
            self.instance = None
            self._create_object(data)

    def __cmap_markers(self,
                       vertex_colors: ndarray) -> None:

        nb_marker = vertex_colors.shape[0]
        nb_dof_marker = asarray(self.instance.vertices).shape[0] // nb_marker
        alpha = 1 if not 0. <= self._object_data['alpha'] <= 1. else self._object_data['alpha']
        transformed_vertex_color = concatenate(tuple(tile(color, (nb_dof_marker, 1)) for color in vertex_colors))
        self.instance.vertex_colors = o3d.utility.Vector3dVector(transformed_vertex_color)
        self.material.base_color = array([1., 1., 1., alpha])

    ########
    # TEXT #
    ########

    def __create_text(self,
                      data: Dict[str, Any]) -> None:

        # Create font style
        data['size'] = 10 if data['size'] == -1. else data['size']
        data['font'] = 'monospace' if data['font'] == '' else data['font']
        # if data['bold'] and data['italic']:
        #     style = gui.FontStyle.BOLD_ITALIC
        # elif data['bold'] or data['italic']:
        #     style = gui.FontStyle.BOLD if data['bold'] else gui.FontStyle.ITALIC
        # else:
        #     style = gui.FontStyle.NORMAL
        # font = gui.FontDescription(typeface=data['font'].lower(), style=style, point_size=data['size'])
        # font_id = gui.Application.instance.add_font(font)

        # Get color
        color = list(get_color(rgb=data['c']))

        # Create instance
        self.instance = gui.Label(data['content'])
        # self.instance.font_id = font_id
        self.instance.background_color = gui.Color(a=0)
        self.instance.text_color = gui.Color(*color)

    def __update_text(self,
                      data: Dict[str, Any],
                      updated_fields: List[str]) -> None:

        # Update content
        if 'content' in updated_fields:
            self.instance.text = data['content']

        # Update position
        if 'gui' in updated_fields:
            size, rect = data['gui']
            # Avoid to print on settings
            data['corner'] = 'BR' if data['corner'] == 'TR' else data['corner']
            # X position
            if data['corner'][1] == 'L':
                x = rect.get_left()
            elif data['corner'][1] == 'M':
                x = (rect.get_right() - size.width) / 2
            else:
                x = rect.get_right() - size.width
            # Y position
            if data['corner'][0] == 'T':
                y = rect.get_top()
            elif data['corner'][0] == 'M':
                y = (rect.get_bottom() - size.height) / 2
            else:
                y = rect.get_bottom() - size.height

            self.instance.frame = gui.Rect(x, y, 2 * size.width, 2 * size.height)

    def __cmap_text(self,
                    vertex_colors: ndarray) -> None:
        pass
