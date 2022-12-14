import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering



class Settings:
    UNLIT = "defaultUnlit"
    LIT = "defaultLit"
    NORMALS = "normals"
    DEPTH = "depth"

    DEFAULT_PROFILE_NAME = "Bright day with sun at +Y [default]"
    POINT_CLOUD_PROFILE_NAME = "Cloudy day (no direct sun)"
    CUSTOM_PROFILE_NAME = "Custom"
    LIGHTING_PROFILES = {
        DEFAULT_PROFILE_NAME: {"ibl_intensity": 45000,
                               "sun_intensity": 45000,
                               "sun_dir": [0.577, -0.577, -0.577],
                               "use_ibl": True,
                               "use_sun": True},
        "Bright day with sun at -Y": {"ibl_intensity": 45000,
                                      "sun_intensity": 45000,
                                      "sun_dir": [0.577, 0.577, 0.577],
                                      "use_ibl": True,
                                      "use_sun": True},
        "Bright day with sun at +Z": {"ibl_intensity": 45000,
                                      "sun_intensity": 45000,
                                      "sun_dir": [0.577, 0.577, -0.577],
                                      "use_ibl": True,
                                      "use_sun": True},
        "Less Bright day with sun at +Y": {"ibl_intensity": 35000,
                                           "sun_intensity": 50000,
                                           "sun_dir": [0.577, -0.577, -0.577],
                                           "use_ibl": True,
                                           "use_sun": True},
        "Less Bright day with sun at -Y": {"ibl_intensity": 35000,
                                           "sun_intensity": 50000,
                                           "sun_dir": [0.577, 0.577, 0.577],
                                           "use_ibl": True,
                                           "use_sun": True},
        "Less Bright day with sun at +Z": {"ibl_intensity": 35000,
                                           "sun_intensity": 50000,
                                           "sun_dir": [0.577, 0.577, -0.577],
                                           "use_ibl": True,
                                           "use_sun": True},
        POINT_CLOUD_PROFILE_NAME: {"ibl_intensity": 60000,
                                   "sun_intensity": 50000,
                                   "use_ibl": True,
                                   "use_sun": False},
    }

    DEFAULT_MATERIAL_NAME = "Polished ceramic [default]"
    PREFAB = {
        DEFAULT_MATERIAL_NAME: {"metallic": 0.0,
                                "roughness": 0.7,
                                "reflectance": 0.5,
                                "clearcoat": 0.2,
                                "clearcoat_roughness": 0.2,
                                "anisotropy": 0.0},
        "Metal (rougher)": {"metallic": 1.0,
                            "roughness": 0.5,
                            "reflectance": 0.9,
                            "clearcoat": 0.0,
                            "clearcoat_roughness": 0.0,
                            "anisotropy": 0.0},
        "Metal (smoother)": {"metallic": 1.0,
                             "roughness": 0.3,
                             "reflectance": 0.9,
                             "clearcoat": 0.0,
                             "clearcoat_roughness": 0.0,
                             "anisotropy": 0.0},
        "Plastic": {"metallic": 0.0,
                    "roughness": 0.5,
                    "reflectance": 0.5,
                    "clearcoat": 0.5,
                    "clearcoat_roughness": 0.2,
                    "anisotropy": 0.0},
        "Glazed ceramic": {"metallic": 0.0,
                           "roughness": 0.5,
                           "reflectance": 0.9,
                           "clearcoat": 1.0,
                           "clearcoat_roughness": 0.1,
                           "anisotropy": 0.0},
        "Clay": {"metallic": 0.0,
                 "roughness": 1.0,
                 "reflectance": 0.5,
                 "clearcoat": 0.1,
                 "clearcoat_roughness": 0.287,
                 "anisotropy": 0.0},
    }

    def __init__(self):
        self.mouse_model = gui.SceneWidget.Controls.ROTATE_CAMERA
        self.bg_color = gui.Color(1, 1, 1)
        self.show_skybox = False
        self.show_axes = False
        self.use_ibl = True
        self.use_sun = True
        self.new_ibl_name = None  # clear to None after loading
        self.ibl_intensity = 45000
        self.sun_intensity = 45000
        self.sun_dir = [0.577, -0.577, -0.577]
        self.sun_color = gui.Color(1, 1, 1)

        self.apply_material = True  # clear to False after processing
        self._materials = {
            Settings.LIT: rendering.MaterialRecord(),
            Settings.UNLIT: rendering.MaterialRecord(),
            Settings.NORMALS: rendering.MaterialRecord(),
            Settings.DEPTH: rendering.MaterialRecord()
        }
        self._materials[Settings.LIT].base_color = [0.9, 0.9, 0.9, 1.0]
        self._materials[Settings.LIT].shader = Settings.LIT
        self._materials[Settings.UNLIT].base_color = [0.9, 0.9, 0.9, 1.0]
        self._materials[Settings.UNLIT].shader = Settings.UNLIT
        self._materials[Settings.NORMALS].shader = Settings.NORMALS
        self._materials[Settings.DEPTH].shader = Settings.DEPTH

        # Conveniently, assigning from self._materials[...] assigns a reference,
        # not a copy, so if we change the property of a material, then switch
        # to another one, then come back, the old setting will still be there.
        self.material = self._materials[Settings.LIT]

    def set_material(self, name):
        self.material = self._materials[name]
        self.apply_material = True

    def apply_material_prefab(self, name):
        assert (self.material.shader == Settings.LIT)
        prefab = Settings.PREFAB[name]
        for key, val in prefab.items():
            setattr(self.material, "base_" + key, val)

    def apply_lighting_profile(self, name):
        profile = Settings.LIGHTING_PROFILES[name]
        for key, val in profile.items():
            setattr(self, key, val)


class AppWindow:
    MENU_OPEN = 1
    MENU_EXPORT = 2
    MENU_QUIT = 3
    MENU_SHOW_SETTINGS = 11
    MENU_ABOUT = 21

    DEFAULT_IBL = "default"

    MATERIAL_NAMES = ["Lit", "Unlit", "Normals", "Depth"]
    MATERIAL_SHADERS = [Settings.LIT, Settings.UNLIT, Settings.NORMALS, Settings.DEPTH]

    def _create_settings(self):

        app = gui.Application.instance
        app.initialize()

        self._window = self.__window = app.create_window("Open3D", 1080, 720)
        self._scene = o3d.visualization.gui.SceneWidget()
        self._scene.scene = o3d.visualization.rendering.Open3DScene(self._window.renderer)
        self._scene.set_on_sun_direction_changed(self._on_sun_dir)

        self._settings = Settings()
        self._settings.new_ibl_name = app.resource_path

        em = self._window.theme.font_size

        self._settings_panel = gui.Vert(0, gui.Margins(*[0.25 * em] * 4))
        self._create_view_settings(em)


        self._window.set_on_layout(self._on_layout)
        self._window.add_child(self._scene)
        self._window.add_child(self._settings_panel)

    def _create_view_settings(self, em):

        view_ctrls = gui.CollapsableVert("View controls", 0.25 * em, gui.Margins(em, 0, 0, 0))
        arcball_button = gui.Button("Arcball")
        arcball_button.horizontal_padding_em, arcball_button.vertical_padding_em = 0.5, 0
        arcball_button.set_on_clicked(self._set_mouse_mode_rotate)
        fly_button = gui.Button("Fly")
        fly_button.horizontal_padding_em, fly_button.vertical_padding_em = 0.5, 0
        fly_button.set_on_clicked(self._set_mouse_mode_fly)
        sun_button = gui.Button("Sun")
        sun_button.horizontal_padding_em, sun_button.vertical_padding_em = 0.5, 0
        sun_button.set_on_clicked(self._set_mouse_mode_sun)
        ibl_button = gui.Button("Environment")
        ibl_button.horizontal_padding_em, ibl_button.vertical_padding_em = 0.5, 0
        ibl_button.set_on_clicked(self._set_mouse_mode_ibl)
        view_ctrls.add_child(gui.Label("Mouse controls"))
        h = gui.Horiz(0.25 * em)
        h.add_stretch()
        h.add_child(arcball_button)
        h.add_child(fly_button)
        h.add_stretch()
        view_ctrls.add_child(h)
        h = gui.Horiz(0.25 * em)
        h.add_stretch()
        h.add_child(sun_button)
        h.add_child(ibl_button)
        h.add_stretch()
        view_ctrls.add_child(h)
        separation_height = int(round(0.5 * em))
        self._show_skybox = gui.Checkbox("Show skymap")
        self._show_skybox.set_on_checked(self._on_show_skybox)
        view_ctrls.add_fixed(separation_height)
        view_ctrls.add_child(self._show_skybox)

        self._bg_color = gui.ColorEdit()
        self._bg_color.set_on_value_changed(self._on_bg_color)

        self._settings_panel.add_child(view_ctrls)

    def _apply_settings(self):
        bg_color = [self._settings.bg_color.red, self._settings.bg_color.green,
                    self._settings.bg_color.blue, self._settings.bg_color.alpha]
        self._scene.scene.set_background(bg_color)
        self._scene.scene.show_skybox(self._settings.show_skybox)
        self._scene.scene.show_axes(self._settings.show_axes)
        if self._settings.new_ibl_name is not None:
            self._scene.scene.scene.set_indirect_light(
                self._settings.new_ibl_name)
            # Clear new_ibl_name, so we don't keep reloading this image every
            # time the settings are applied.
            self._settings.new_ibl_name = None
        self._scene.scene.scene.enable_indirect_light(self._settings.use_ibl)
        self._scene.scene.scene.set_indirect_light_intensity(
            self._settings.ibl_intensity)
        sun_color = [
            self._settings.sun_color.red, self._settings.sun_color.green,
            self._settings.sun_color.blue
        ]
        self._scene.scene.scene.set_sun_light(self._settings.sun_dir, sun_color,
                                              self._settings.sun_intensity)
        self._scene.scene.scene.enable_sun_light(self._settings.use_sun)

        if self._settings.apply_material:
            self._scene.scene.update_material(self._settings.material)
            self._settings.apply_material = False

        # self._bg_color.color_value = self._settings.bg_color
        # self._show_skybox.checked = self._settings.show_skybox
        # self._show_axes.checked = self._settings.show_axes
        # self._use_ibl.checked = self._settings.use_ibl
        # self._use_sun.checked = self._settings.use_sun
        # self._ibl_intensity.int_value = self._settings.ibl_intensity
        # self._sun_intensity.int_value = self._settings.sun_intensity
        # self._sun_dir.vector_value = self._settings.sun_dir
        # self._sun_color.color_value = self._settings.sun_color
        # self._material_prefab.enabled = (
        #         self._settings.material.shader == Settings.LIT)
        # c = gui.Color(self._settings.material.base_color[0],
        #               self._settings.material.base_color[1],
        #               self._settings.material.base_color[2],
        #               self._settings.material.base_color[3])
        # self._material_color.color_value = c
        # self._point_size.double_value = self._settings.material.point_size

    def _on_layout(self, layout_context):

        r = self._window.content_rect
        self._scene.frame = r
        width = 17 * layout_context.theme.font_size
        height = min(r.height,
                     self._settings_panel.calc_preferred_size(layout_context,
                                                              o3d.visualization.gui.Widget.Constraints()).height)
        self._settings_panel.frame = o3d.visualization.gui.Rect(r.get_right() - width, r.y, width, height)

    def _on_sun_dir(self, sun_dir):

        self._settings.sun_dir = sun_dir
        self._profiles.selected_text = Settings.CUSTOM_PROFILE_NAME
        self._apply_settings()

    def _set_mouse_mode_rotate(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_CAMERA)

    def _set_mouse_mode_fly(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.FLY)

    def _set_mouse_mode_sun(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_SUN)

    def _set_mouse_mode_ibl(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_IBL)

    def _on_show_skybox(self, show):
        self._settings.show_skybox = show
        self._apply_settings()

    def _on_bg_color(self, new_color):
        self._settings.bg_color = new_color
        self._apply_settings()
