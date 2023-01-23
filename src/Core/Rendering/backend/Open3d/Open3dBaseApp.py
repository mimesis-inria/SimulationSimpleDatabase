import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
from glob import glob
from os.path import join, basename


class Settings:

    def __init__(self):

        self.bg_color = gui.Color(1, 1, 1)
        self.show_skymap = False
        self.show_axes = False
        self.show_ground = False
        self.skymap_name = None
        self.use_skymap_light = True
        self.use_sun_light = True
        self.skymap_intensity = 45000
        self.sun_intensity = 45000
        self.sun_dir = [0.577, -0.577, -0.577]
        self.sun_color = gui.Color(1, 1, 1)


class BaseApp:
    additional_labels = {}

    def _create_settings(self, nb_group):

        app = gui.Application.instance
        app.initialize()

        self._window = self.__window = app.create_window("Open3D", 1080, 720)
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(self._window.renderer)
        self._scene.set_on_sun_direction_changed(self.__on_sun_dir)

        em = self._window.theme.font_size
        self._settings = Settings()
        self._settings_panel = gui.Vert(0, gui.Margins(*[0.25 * em] * 4))
        self.__create_view_settings(em)
        self.__create_light_settings(em)
        self.__create_group_settings(nb_group, em)
        self.__apply_settings()
        self.__create_menu()

        self._window.set_on_layout(self.__on_layout)
        self._window.add_child(self._scene)
        self._window.add_child(self._settings_panel)

    def __create_view_settings(self, em):

        # View section
        view = gui.CollapsableVert('View', 0.25 * em, gui.Margins(em, 0, 0, 0))
        view.set_is_open(False)
        separation_height = int(round(0.5 * em))

        # Camera control settings
        view.add_child(gui.Label('Mouse Controls'))
        line = gui.Horiz(0.25 * em)
        line.add_stretch()
        model_button = gui.Button('Model')
        model_button.horizontal_padding_em, model_button.vertical_padding_em = 0.5, 0
        model_button.set_on_clicked(self.__on_mouse_mode_model)
        line.add_child(model_button)
        sun_button = gui.Button('Sun')
        sun_button.horizontal_padding_em, sun_button.vertical_padding_em = 0.5, 0
        sun_button.set_on_clicked(self.__on_mouse_mode_sun)
        line.add_child(sun_button)
        env_button = gui.Button('Skymap')
        env_button.horizontal_padding_em, env_button.vertical_padding_em = 0.5, 0
        env_button.set_on_clicked(self.__on_mouse_mode_skymap)
        line.add_child(env_button)
        line.add_stretch()
        view.add_child(line)

        # Background settings
        view.add_fixed(separation_height)
        view.add_child(gui.Label('Background Color'))
        self._bg_color_widget = gui.ColorEdit()
        self._bg_color_widget.set_on_value_changed(self.__on_bg_color)
        view.add_child(self._bg_color_widget)

        # Skymap settings
        view.add_fixed(separation_height)
        view.add_child(gui.Label('Skymap'))
        line = gui.VGrid(2, 0.25 * em)
        self._show_skymap_widget = gui.Checkbox('Show Skymap')
        self._show_skymap_widget.set_on_checked(self.__on_show_skymap)
        line.add_child(self._show_skymap_widget)
        self._skymap_name_widget = gui.Combobox()
        for ibl in sorted(glob(join(gui.Application.instance.resource_path, '*_ibl.ktx'))):
            self._skymap_name_widget.add_item(basename(ibl[:-8]))
        self._skymap_name_widget.selected_text = 'default'
        self._skymap_name_widget.set_on_selection_changed(self.__on_skymap_name)
        line.add_child(self._skymap_name_widget)
        view.add_child(line)

        # Axes settings
        view.add_fixed(separation_height)
        view.add_child(gui.Label('Axes'))
        line = gui.VGrid(2, 0.25 * em)
        self._show_axes_widget = gui.Checkbox('Show Axes')
        self._show_axes_widget.set_on_checked(self.__on_show_axes)
        line.add_child(self._show_axes_widget)
        self._show_ground_widget = gui.Checkbox('Show Ground')
        self._show_ground_widget.set_on_checked(self.__on_show_ground)
        line.add_child(self._show_ground_widget)
        view.add_child(line)
        view.add_fixed(separation_height)

        # Add view section
        self._settings_panel.add_fixed(separation_height)
        self._settings_panel.add_child(view)

    def __create_light_settings(self, em):

        # Light section
        light = gui.CollapsableVert('Lighting', 0, gui.Margins(em, 0, 0, 0))
        light.set_is_open(False)
        separation_height = int(round(0.5 * em))

        # Skymap light settings
        light.add_child(gui.Label('Skymap Light'))
        self._use_skymap_light_widget = gui.Checkbox('Enable light source')
        self._use_skymap_light_widget.set_on_checked(self.__on_use_skymap_light)
        light.add_child(self._use_skymap_light_widget)
        line = gui.VGrid(2, 0.25 * em)
        line.add_child(gui.Label('Intensity'))
        self._skymap_intensity_widget = gui.Slider(gui.Slider.INT)
        self._skymap_intensity_widget.set_limits(0, 200000)
        self._skymap_intensity_widget.set_on_value_changed(self.__on_skymap_intensity)
        line.add_child(self._skymap_intensity_widget)
        light.add_fixed(separation_height)
        light.add_child(line)

        # Sunlight settings
        light.add_fixed(separation_height)
        light.add_child(gui.Label('Sun Light'))
        self._use_sun_light_widget = gui.Checkbox('Enable light source')
        self._use_sun_light_widget.set_on_checked(self.__on_use_sun_light)
        light.add_child(self._use_sun_light_widget)
        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label('Intensity'))
        self._sun_intensity_widget = gui.Slider(gui.Slider.INT)
        self._sun_intensity_widget.set_limits(0, 200000)
        self._sun_intensity_widget.set_on_value_changed(self.__on_sun_intensity)
        grid.add_child(self._sun_intensity_widget)
        grid.add_child(gui.Label('Direction'))
        self._sun_dir_widget = gui.VectorEdit()
        self._sun_dir_widget.set_on_value_changed(self.__on_sun_dir)
        grid.add_child(self._sun_dir_widget)
        grid.add_child(gui.Label('Color'))
        self._sun_color_widget = gui.ColorEdit()
        self._sun_color_widget.set_on_value_changed(self.__on_sun_color)
        grid.add_child(self._sun_color_widget)
        light.add_fixed(separation_height)
        light.add_child(grid)

        # Add light section
        self._settings_panel.add_fixed(2 * separation_height)
        self._settings_panel.add_child(light)

    def __create_group_settings(self, nb_group, em):

        # Groups section
        separation_height = int(round(0.5 * em))
        groups = gui.CollapsableVert('Groups', 0, gui.Margins(em, 0, 0, 0))
        groups.set_is_open(True)

        # Groups settings
        line = gui.VGrid(2, 0.25 * em)
        line.add_child(gui.Label('Display group'))
        group_widget = gui.Combobox()
        for group in range(1, nb_group + 1):
            group_widget.add_item(str(group))
        group_widget.selected_text = '1'
        group_widget.set_on_selection_changed(self.__on_group)
        line.add_child(group_widget)
        groups.add_child(line)

        # Add groups section
        self._settings_panel.add_fixed(2 * separation_height)
        self._settings_panel.add_child(groups)

    def __apply_settings(self):

        # View settings
        bg_color = [self._settings.bg_color.red, self._settings.bg_color.green, self._settings.bg_color.blue,
                    self._settings.bg_color.alpha]
        self._scene.scene.set_background(bg_color)
        self._scene.scene.show_skybox(self._settings.show_skymap)
        self._scene.scene.show_axes(self._settings.show_axes)
        self._scene.scene.show_ground_plane(self._settings.show_ground, rendering.Scene.GroundPlane(0))

        # Skymap light settings
        if self._settings.skymap_name is not None:
            self._scene.scene.scene.set_indirect_light(self._settings.skymap_name)
            self._settings.skymap_name = None
        self._scene.scene.scene.enable_indirect_light(self._settings.use_skymap_light)
        self._scene.scene.scene.set_indirect_light_intensity(self._settings.skymap_intensity)

        # Sunlight settings
        sun_color = [self._settings.sun_color.red, self._settings.sun_color.green, self._settings.sun_color.blue]
        self._scene.scene.scene.set_sun_light(self._settings.sun_dir, sun_color, self._settings.sun_intensity)
        self._scene.scene.scene.enable_sun_light(self._settings.use_sun_light)

        # Update widgets
        self._bg_color_widget.color_value = self._settings.bg_color
        self._show_skymap_widget.checked = self._settings.show_skymap
        self._show_axes_widget.checked = self._settings.show_axes
        self._show_ground_widget.checked = self._settings.show_ground
        self._use_skymap_light_widget.checked = self._settings.use_skymap_light
        self._use_sun_light_widget.checked = self._settings.use_sun_light
        self._skymap_intensity_widget.int_value = self._settings.skymap_intensity
        self._sun_intensity_widget.int_value = self._settings.sun_intensity
        self._sun_dir_widget.vector_value = self._settings.sun_dir
        self._sun_color_widget.color_value = self._settings.sun_color

    def __create_menu(self):

        if gui.Application.instance.menubar is None:
            app_menu = gui.Menu()
            app_menu.add_item('Show Settings', 1)
            app_menu.set_checked(1, True)
            app_menu.add_separator()
            app_menu.add_item('Quit', 2)
            menu = gui.Menu()
            menu.add_menu('Menu', app_menu)
            gui.Application.instance.menubar = menu

        self._window.set_on_menu_item_activated(1, self.__on_menu_show)
        self._window.set_on_menu_item_activated(2, self.__on_menu_quit)

    def __on_layout(self, layout_context):

        r = self._window.content_rect
        self._scene.frame = r
        width = 17 * layout_context.theme.font_size
        height = min(r.height, self._settings_panel.calc_preferred_size(layout_context,
                                                                        gui.Widget.Constraints()).height)
        self._settings_panel.frame = gui.Rect(r.get_right() - width, r.y, width, height)

        for actor in self.additional_labels.values():
            size = actor.instance.calc_preferred_size(layout_context, gui.Widget.Constraints())
            actor.update_data(data={'gui': [size, r]})
            actor.update()

    def __on_mouse_mode_model(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_CAMERA)

    def __on_mouse_mode_sun(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_SUN)

    def __on_mouse_mode_skymap(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_IBL)

    def __on_bg_color(self, new_color):
        self._settings.bg_color = new_color
        self.__apply_settings()

    def __on_show_skymap(self, show):
        self._settings.show_skymap = show
        self.__apply_settings()

    def __on_skymap_name(self, name, _):
        self._settings.skymap_name = gui.Application.instance.resource_path + "/" + name
        self.__apply_settings()

    def __on_show_axes(self, show):
        self._settings.show_axes = show
        self.__apply_settings()

    def __on_show_ground(self, show):
        self._settings.show_ground = show
        self.__apply_settings()

    def __on_use_skymap_light(self, use):
        self._settings.use_skymap_light = use
        self.__apply_settings()

    def __on_skymap_intensity(self, intensity):
        self._settings.skymap_intensity = int(intensity)
        self.__apply_settings()

    def __on_use_sun_light(self, use):
        self._settings.use_sun_light = use
        self.__apply_settings()

    def __on_sun_intensity(self, intensity):
        self._settings.sun_intensity = int(intensity)
        self.__apply_settings()

    def __on_sun_dir(self, sun_dir):
        self._settings.sun_dir = sun_dir
        self.__apply_settings()

    def __on_sun_color(self, color):
        self._settings.sun_color = color
        self.__apply_settings()

    def __on_group(self, _, index):
        self._change_group(index)

    def _change_group(self, index):
        raise NotImplementedError

    def __on_menu_show(self):
        self._settings_panel.visible = not self._settings_panel.visible
        gui.Application.instance.menubar.set_checked(1, self._settings_panel.visible)

    def __on_menu_quit(self):
        self.exit()

    def exit(self, force_quit: bool = True):
        pass
