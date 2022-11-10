from typing import Any, Optional, Dict
from numpy import array, tile
from vedo import Mesh, Points, Arrows, Marker, Glyph


class VedoActor:

    def __init__(self,
                 visualizer: any,
                 actor_type: str,
                 window: int):

        # Actor information
        self.visualizer: Any = visualizer
        self.at: int = window
        self.actor_type: str = actor_type
        self.actor_data: Optional[Dict[str, Any]] = None
        self.cmap_data: Optional[Dict[str, Any]] = None
        self.instance: Optional[Points] = None

        # Select the good method according to the Actor type
        create = {'Mesh': self.__create_mesh,
                  'Points': self.__create_points,
                  'Arrows': self.__create_arrows,
                  'Markers': self.__create_markers,
                  'Symbols': self.__create_symbols}
        update = {'Mesh': self.__update_mesh,
                  'Points': self.__update_points,
                  'Arrows': self.__update_arrows,
                  'Markers': self.__update_markers,
                  'Symbols': self.__update_symbols}
        self.create = create[self.actor_type]
        self.update = update[self.actor_type]

    def apply_cmap(self,
                   data: Dict[str, Any]):

        # Register cmap data
        if self.cmap_data is None:
            self.cmap_data = data
        for key, value in data.items():
            if value is not None:
                self.cmap_data[key] = value

        # Apply cmap if scalar field is defined
        if len(self.cmap_data['scalar_field']) > 0:
            self.instance.cmap(cname=self.cmap_data['colormap'],
                               input_array=self.cmap_data['scalar_field'][0])

        return self.instance

    ########
    # MESH #
    ########

    def __create_mesh(self,
                      data: Dict[str, Any]):

        # Register Actor data
        self.actor_data = data
        # Create instance
        self.instance = Mesh(inputobj=[data['positions'], data['cells']],
                             c=data['c'],
                             alpha=data['alpha'])
        self.instance.compute_normals(data['compute_normals']).lw(data['line_width']).wireframe(data['wireframe'])
        return self

    def __update_mesh(self,
                      data: Dict[str, Any]):

        # Register Actor data
        for key, value in data.items():
            if value is not None:
                self.actor_data[key] = value
        # Update instance
        self.instance.points(self.actor_data['positions']).lw(self.actor_data['line_width'])\
            .wireframe(self.actor_data['wireframe']).alpha(self.actor_data['alpha']).c(self.actor_data['c'])
        return self

    ##########
    # POINTS #
    ##########

    def __create_points(self,
                        data: Dict[str, Any]):

        # Register Actor data
        self.actor_data = data
        # Create instance
        self.instance = Points(inputobj=data['positions'],
                               r=data['point_size'],
                               c=data['c'],
                               alpha=data['alpha'])
        return self

    def __update_points(self,
                        data: Dict[str, Any]):

        # Register Actor data
        for key, value in data.items():
            if value is not None:
                self.actor_data[key] = value
        # Update instance
        self.instance.points(self.actor_data['positions']).ps(self.actor_data['point_size'])\
            .alpha(self.actor_data['alpha']).c(self.actor_data['c'])
        return self

    ##########
    # ARROWS #
    ##########

    def __create_arrows(self,
                        data: Dict[str, Any]):

        # Register Actor data
        self.actor_data = data
        # Create instance
        self.instance = Arrows(start_pts=data['positions'],
                               end_pts=data['positions'] + data['vectors'],
                               res=data['res'],
                               c=data['c'],
                               alpha=data['alpha'])
        return self

    def __update_arrows(self,
                        data: Dict[str, Any]):

        # Register Actor data
        for key, value in data.items():
            if value is not None:
                self.actor_data[key] = value
        # Re-create instance
        self.instance = Arrows(start_pts=self.actor_data['positions'],
                               end_pts=self.actor_data['positions'] + self.actor_data['vectors'],
                               res=self.actor_data['res'],
                               c=self.actor_data['c'],
                               alpha=self.actor_data['alpha'])
        return self

    ###########
    # MARKERS #
    ###########

    def __create_markers(self,
                         data: Dict[str, Any]):

        # Register Actor data
        self.actor_data = data
        # Get orientation information
        normal_to = self.visualizer.get_actor(data['normal_to']).instance
        positions = normal_to.points()[data['indices']][0]
        orientations = normal_to.normals()[data['indices']][0]
        # Create instance
        marker = Marker(symbol=data['symbol'],
                        s=data['size'],
                        filled=data['filled']).orientation(newaxis=[1, 0, 0], rotation=90, rad=False)
        self.instance = Glyph(mesh=positions,
                              glyphObj=marker,
                              orientation_array=orientations,
                              c=data['c'],
                              alpha=data['alpha'])
        return self

    def __update_markers(self,
                         data: Dict[str, Any]):

        # Register Actor data
        for key, value in data.items():
            if value is not None:
                self.actor_data[key] = value
        # Get orientation information
        normal_to = self.visualizer.get_actor(self.actor_data['normal_to']).instance
        positions = normal_to.points()[self.actor_data['indices']][0]
        orientations = normal_to.normals()[self.actor_data['indices']][0]
        # Re-create instance
        marker = Marker(symbol=self.actor_data['symbol'],
                        s=self.actor_data['size'],
                        filled=self.actor_data['filled']).orientation(newaxis=[1, 0, 0], rotation=90, rad=False)
        self.instance = Glyph(mesh=positions,
                              glyphObj=marker,
                              orientation_array=orientations,
                              c=self.actor_data['c'],
                              alpha=self.actor_data['alpha'])
        return self

    ###########
    # SYMBOLS #
    ###########

    def __create_symbols(self,
                         data: Dict[str, Any]):

        # Get orientation information
        if data['orientations'].shape == (1, 3):
            data['orientations'] = tile(data['orientations'][0], (len(data['positions']), 1))
        else:
            data['orientations'] = tile(array([1, 0, 0]), (len(data['positions']), 1))
        # Register Actor data
        self.actor_data = data
        # Create instance
        marker = Marker(symbol=data['symbol'],
                        s=data['size'],
                        filled=data['filled']).orientation(newaxis=[1, 0, 0], rotation=90, rad=False)
        self.instance = Glyph(mesh=data['positions'],
                              glyphObj=marker,
                              orientation_array=data['orientations'],
                              c=data['c'],
                              alpha=data['alpha'])
        return self

    def __update_symbols(self,
                         data: Dict[str, Any]):

        # Get orientation information
        if 'orientations' in data and data['orientations'] is not None:
            pos = data['positions'] if 'positions' in data and data['positions'] is not None\
                else self.actor_data['positions']
            if data['orientations'].shape == (1, 3):
                data['orientations'] = tile(data['orientations'][0], (len(pos), 1))
            else:
                data['orientations'] = tile(array([1, 0, 0]), (len(pos), 1))
        # Register Actor data
        for key, value in data.items():
            if value is not None:
                self.actor_data[key] = value
        # Re-create instance
        marker = Marker(symbol=self.actor_data['symbol'],
                        s=self.actor_data['size'],
                        filled=self.actor_data['filled']).orientation(newaxis=[1, 0, 0], rotation=90, rad=False)
        self.instance = Glyph(mesh=self.actor_data['positions'],
                              glyphObj=marker,
                              orientation_array=self.actor_data['orientations'],
                              c=self.actor_data['c'],
                              alpha=self.actor_data['alpha'])
        return self
