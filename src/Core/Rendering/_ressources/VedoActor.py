from typing import Any, Optional, Dict, List
from numpy import array, tile
from vedo import Mesh, Points, Arrows, Marker, Glyph, Text2D
from numpy.linalg import norm
from matplotlib.colors import Normalize
from matplotlib.pyplot import get_cmap

from SSD.Core.Rendering._ressources._Actor import _Actor


class VedoActor(_Actor):

    def __init__(self,
                 actor_type: str,
                 actor_name: str,
                 actor_group: int):
        """

        :param actor_type:
        :param actor_name:
        :param actor_group:
        """

        _Actor.__init__(self, actor_type=actor_type, actor_name=actor_name, actor_group=actor_group)

        # Actor information
        self.instance: Optional[Points] = None

        # Actor specialization
        spec = {'Mesh': (self.__create_mesh, self.__update_mesh),
                'Points': (self.__create_points, self.__update_points),
                'Arrows': (self.__create_arrows, self.__update_arrows),
                'Markers': (self.__create_markers, self.__update_markers),
                'Text': (self.__create_text, self.__update_text)}
        self._create_object = spec[self.type][0]
        self._update_object = spec[self.type][1]

    def apply_cmap(self,
                   data: Dict[str, Any]) -> None:

        if self.type in ['Mesh', 'Points']:
            self.instance.cmap(cname=data['colormap'],
                               input_array=data['scalar_field'][0])
        elif self.type in ['Arrows', 'Markers']:
            full_data = self._object_data.copy()
            for key, value in data.items():
                full_data[key] = value
            self._create_object(full_data)

    ########
    # MESH #
    ########

    def __create_mesh(self,
                      data: Dict[str, Any]):

        # Create instance
        self.instance = Mesh(inputobj=[data['positions'], data['cells']],
                             c=data['c'],
                             alpha=data['alpha'])
        self.instance.compute_normals(data['compute_normals']).lw(data['line_width']).wireframe(data['wireframe'])

    def __update_mesh(self,
                      data: Dict[str, Any],
                      updated_fields: List[str]):

        # Update instance
        if 'positions' in updated_fields:
            self.instance.points(data['positions'])
        if 'line_width' in updated_fields or 'wireframe' in updated_fields:
            self.instance.lw(data['line_width']).wireframe(data['wireframe'])
        if 'alpha' in updated_fields or 'c' in updated_fields:
            self.instance.alpha(data['alpha']).c(data['c'])

    ##########
    # POINTS #
    ##########

    def __create_points(self,
                        data: Dict[str, Any]):

        # Create instance
        self.instance = Points(inputobj=data['positions'],
                               r=data['point_size'],
                               c=data['c'],
                               alpha=data['alpha'])

    def __update_points(self,
                        data: Dict[str, Any],
                        updated_fields: List[str]):

        # Update instance
        if 'positions' in updated_fields:
            self.instance.points(data['positions'])
        if 'point_size' in updated_fields:
            self.instance.ps(data['point_size'])
        if 'alpha' in updated_fields or 'c' in updated_fields:
            self.instance.alpha(data['alpha']).c(data['c'])

    ##########
    # ARROWS #
    ##########

    def __create_arrows(self,
                        data: Dict[str, Any]):

        # Create instance
        if 'scalar_field' in data:
            scalar_field = data['scalar_field']
            cmap_norm = Normalize(vmin=min(scalar_field[0]),
                                  vmax=max(scalar_field[0]))
            cmap = get_cmap(data['colormap'])
            applied_colors = cmap(cmap_norm(scalar_field[0]))[:, 0:3]
        else:
            applied_colors = data['c']

        self.instance = Arrows(start_pts=data['positions'],
                               end_pts=data['positions'] + data['vectors'],
                               res=data['res'],
                               c=applied_colors,
                               alpha=data['alpha'])

    def __update_arrows(self,
                        data: Dict[str, Any],
                        updated_fields: List[str]):

        # Re-create instance
        if 'positions' in updated_fields or 'vectors' in updated_fields:
            self._create_object(data)
        elif 'alpha' in updated_fields or 'c' in updated_fields:
            self.instance.alpha(data['alpha']).c(data['c'])

    ###########
    # MARKERS #
    ###########

    def __create_markers(self,
                         data: Dict[str, Any]):

        # Get orientation information
        normal_to = data['normal_to']
        positions = normal_to.instance.points()[data['indices']][0]
        orientations = normal_to.instance.normals()[data['indices']][0]
        # Create instance
        marker = Marker(symbol=data['symbol'],
                        s=data['size'],
                        filled=data['filled']).orientation(newaxis=[1, 0, 0], rotation=90, rad=False)
        if 'scalar_field' in data:
            scalar_field = data['scalar_field']
            cmap_norm = Normalize(vmin=min(scalar_field[0]),
                                  vmax=max(scalar_field[0]))
            cmap = get_cmap(data['colormap'])
            applied_colors = cmap(cmap_norm(scalar_field[0]))[:, 0:3]
        else:
            applied_colors = data['c']

        self.instance = Glyph(mesh=positions,
                              glyph=marker,
                              orientation_array=orientations,
                              c=applied_colors,
                              alpha=data['alpha'])

    def __update_markers(self,
                         data: Dict[str, Any],
                         updated_fields: List[str]):

        if len(updated_fields) > 0 or 'positions' in data['normal_to']._updated_fields:
            self._create_object(data)

    ########
    # TEXT #
    ########

    def __create_text(self,
                      data: Dict[str, Any]):

        # Get Text position
        coord = {'B': 'bottom', 'L': 'left', 'M': 'middle', 'R': 'right', 'T': 'top'}
        corner = data['corner']
        pos = f'{coord[corner[0].upper()]}-{coord[corner[1].upper()]}'

        # Create instance
        self.instance = Text2D(txt=data['content'],
                               pos=pos,
                               s=data['size'],
                               font=data['font'],
                               bold=data['bold'],
                               italic=data['italic'],
                               c=data['c'])
        self.instance.bold()

    def __update_text(self,
                      data: Dict[str, Any],
                      updated_fields: List[str]):

        # Update instance
        if 'content' in updated_fields:
            self.instance.text(data['content'])
        if 'c' in updated_fields:
            self.instance.c(data['c'])
        if 'bold' in updated_fields or 'italic' in updated_fields:
            self.instance.bold(data['bold']).italic(data['italic'])
