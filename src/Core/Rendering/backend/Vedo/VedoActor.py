from typing import Any, Optional, Dict, List
from vedo import Mesh, Points, Arrows, Marker, Glyph, Text2D
from matplotlib.colors import Normalize
from matplotlib.pyplot import get_cmap

from SSD.Core.Rendering.backend.BaseActor import BaseActor


class VedoActor(BaseActor):

    def __init__(self,
                 actor_type: str,
                 actor_name: str,
                 actor_group: int):
        """
        The VedoActor is used to create and update Vedo object instances.

        :param actor_type: Type of the Actor.
        :param actor_name: Name of the Actor.
        :param actor_group: Index of the group of the Actor.
        """

        BaseActor.__init__(self,
                           actor_type=actor_type,
                           actor_name=actor_name,
                           actor_group=actor_group)

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
        """
        General colormap apply method.

        :param data: Colormap data.
        """

        # Use 'cmap' method for Meshes and Points
        if self.type in ['Mesh', 'Points']:
            self.instance.cmap(cname=data['colormap'],
                               input_array=data['scalar_field'][0])

        # Re-create a new object with specified color vector for Arrows and Markers
        elif self.type in ['Arrows', 'Markers']:
            full_data = self._object_data.copy()
            for key, value in data.items():
                full_data[key] = value
            self._create_object(full_data)

    ########
    # MESH #
    ########

    def __create_mesh(self,
                      data: Dict[str, Any]) -> None:

        # Create instance
        self.instance = Mesh(inputobj=[data['positions'], data['cells']],
                             c=data['c'],
                             alpha=data['alpha']).compute_normals()
        # Apply rendering style
        data['line_width'] = 0. if data['line_width'] == -1. else data['line_width']
        self.instance.lw(data['line_width']).wireframe(data['wireframe'])

    def __update_mesh(self,
                      data: Dict[str, Any],
                      updated_fields: List[str]) -> None:

        # Update positions
        if 'positions' in updated_fields:
            self.instance.points(data['positions'])

        # Update rendering style
        if 'line_width' in updated_fields or 'wireframe' in updated_fields:
            data['line_width'] = 0. if data['line_width'] == -1. else data['line_width']
            self.instance.lw(data['line_width']).wireframe(data['wireframe'])

        # Update color
        if 'alpha' in updated_fields or 'c' in updated_fields:
            self.instance.alpha(data['alpha']).c(data['c'])

    ##########
    # POINTS #
    ##########

    def __create_points(self,
                        data: Dict[str, Any]) -> None:

        # Create instance
        self.instance = Points(inputobj=data['positions'],
                               r=data['point_size'],
                               c=data['c'],
                               alpha=data['alpha'])

    def __update_points(self,
                        data: Dict[str, Any],
                        updated_fields: List[str]) -> None:

        # Update positions
        if 'positions' in updated_fields:
            self.instance.points(data['positions'])

        # Update rendering style
        if 'point_size' in updated_fields:
            self.instance.ps(data['point_size'])

        # Update color
        if 'alpha' in updated_fields or 'c' in updated_fields:
            self.instance.alpha(data['alpha']).c(data['c'])

    ##########
    # ARROWS #
    ##########

    def __create_arrows(self,
                        data: Dict[str, Any]) -> None:

        # With a colormap, create a color vector
        if 'scalar_field' in data:
            scalar_field = data['scalar_field']
            cmap_norm = Normalize(vmin=min(scalar_field[0]),
                                  vmax=max(scalar_field[0]))
            cmap = get_cmap(data['colormap'])
            applied_colors = cmap(cmap_norm(scalar_field[0]))[:, 0:3]
        # Otherwise, use the color name
        else:
            applied_colors = data['c']

        # Create instance
        self.instance = Arrows(start_pts=data['positions'],
                               end_pts=data['positions'] + data['vectors'],
                               res=data['res'],
                               c=applied_colors,
                               alpha=data['alpha'])

    def __update_arrows(self,
                        data: Dict[str, Any],
                        updated_fields: List[str]) -> None:

        # Re-create instance to update the vectors
        if 'positions' in updated_fields or 'vectors' in updated_fields:
            self._create_object(data)

        # Update color
        elif 'alpha' in updated_fields or 'c' in updated_fields:
            self.instance.alpha(data['alpha']).c(data['c'])

    ###########
    # MARKERS #
    ###########

    def __create_markers(self,
                         data: Dict[str, Any]) -> None:

        # Get position and orientation information from the associated Actor
        normal_to = data['normal_to']
        positions = normal_to.instance.points()[data['indices']][0]
        orientations = normal_to.instance.normals()[data['indices']][0]

        # Create the Marker object
        marker = Marker(symbol=data['symbol'],
                        s=data['size'],
                        filled=data['filled']).orientation(newaxis=[1, 0, 0], rotation=90, rad=False)

        # With a colormap, create a color vector
        if 'scalar_field' in data:
            scalar_field = data['scalar_field']
            cmap_norm = Normalize(vmin=min(scalar_field[0]),
                                  vmax=max(scalar_field[0]))
            cmap = get_cmap(data['colormap'])
            applied_colors = cmap(cmap_norm(scalar_field[0]))[:, 0:3]
        # Otherwise, use the color name
        else:
            applied_colors = data['c']

        # Create instance
        self.instance = Glyph(mesh=positions,
                              glyph=marker,
                              orientation_array=orientations,
                              c=applied_colors,
                              alpha=data['alpha'])

    def __update_markers(self,
                         data: Dict[str, Any],
                         updated_fields: List[str]) -> None:

        # Re-create instance to update any change (from current Actor or from associated Actor's positions)
        if len(updated_fields) > 0 or 'positions' in data['normal_to'].updated_fields:
            self._create_object(data)

    ########
    # TEXT #
    ########

    def __create_text(self,
                      data: Dict[str, Any]) -> None:

        # Get Text position
        coord = {'B': 'bottom', 'L': 'left', 'M': 'middle', 'R': 'right', 'T': 'top'}
        corner = data['corner']
        pos = f'{coord[corner[0].upper()]}-{coord[corner[1].upper()]}'

        # Create instance
        data['size'] = 1 if data['size'] == -1. else data['size']
        data['font'] = 'Arial' if data['font'] == '' else data['font']
        self.instance = Text2D(txt=data['content'],
                               pos=pos,
                               s=data['size'],
                               font=data['font'],
                               bold=data['bold'],
                               italic=data['italic'],
                               c=data['c'])

    def __update_text(self,
                      data: Dict[str, Any],
                      updated_fields: List[str]) -> None:

        # Update text content
        if 'content' in updated_fields:
            self.instance.text(data['content'])

        # Update rendering style
        if 'bold' in updated_fields or 'italic' in updated_fields:
            self.instance.bold(data['bold']).italic(data['italic'])

        # Update color
        if 'c' in updated_fields:
            self.instance.c(data['c'])
