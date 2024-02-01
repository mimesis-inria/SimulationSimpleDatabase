from typing import Dict
from threading import Thread
from copy import copy
from time import time, sleep
import open3d as o3d

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.backend.base_replay import BaseReplay
from SSD.Core.Rendering.backend.open3d.open3d_app import BaseApp
from SSD.Core.Rendering.backend.open3d.open3d_object import Open3dObject


class Open3dReplay(BaseApp, BaseReplay):

    def __init__(self,
                 database: Database,
                 fps: int = 20):
        """
        Replay a simulation from saved visual data with Open3D.

        :param database: Database to connect to.
        :param fps: Max frame rate.
        """

        BaseReplay.__init__(self,
                            database=database,
                            fps=fps)

        self.objects: Dict[int, Dict[str, Open3dObject]] = {}
        self.__current_group: int = 0
        self.__previous_group: int = 0
        self.__group_change: bool = False
        self.__is_done = False

    def get_object(self,
                   object_name: str) -> Open3dObject:
        """
        Get an Object instance.

        :param object_name: Name of the Object.
        """

        group = self.groups[object_name]
        return self.objects[group][object_name]

    def create_object_backend(self,
                              object_name: str,
                              object_type: str,
                              object_group: int) -> None:
        """
        Specific Object creation instructions.

        :param object_name: Name of the Object.
        :param object_type: Type of the Object.
        :param object_group: Group of the Object.
        """

        self.objects[object_group][object_name] = Open3dObject(object_type=object_type,
                                                               object_name=object_name,
                                                               object_group=object_group)
        if object_type == 'Text':
            self.additional_labels[object_name] = self.objects[object_group][object_name]

    def launch_visualizer(self) -> None:
        """
        Start the Visualizer: create all Objects and render them.
        """

        # 1. Init Visualizer instance
        self._create_settings(len(self.objects))
        self._window.set_on_close(self.close)

        # 2. Add all Text
        for v_object in self.additional_labels.values():
            self._window.add_child(v_object.instance)
            v_object.instance.visible = False

        # 3. Add geometries to the Visualizer
        for v_object in self.objects[self.__current_group].values():
            if v_object.type == 'Text':
                v_object.instance.visible = True
            else:
                self._scene.scene.add_geometry(v_object.name, v_object.instance, v_object.material)
        bounds = self._scene.scene.bounding_box
        self._scene.setup_camera(60, bounds, bounds.get_center())

        # 4. Add Start button
        bu = o3d.visualization.gui.Button('Start')
        bu.set_on_clicked(self.reset)
        separation_height = int(round(self._window.theme.font_size * 0.5))
        self._settings_panel.add_fixed(2 * separation_height)
        self._settings_panel.add_child(bu)

        # 5. Launch mainloop
        Thread(target=self.update_thread).start()
        o3d.visualization.gui.Application.instance.run()

    def update_thread(self) -> None:
        """
        Timer callback to update the rendering view.
        """

        while not self.__is_done:
            self.step += 1
            process_time = time()
            o3d.visualization.gui.Application.instance.post_to_main_thread(self._window,
                                                                           self.__update_thread)
            # Respect frame rate
            dt = max(0., self.fps - (time() - process_time))
            sleep(dt)

        # Close the Visualizer
        o3d.visualization.gui.Application.instance.quit()

    def __update_thread(self) -> None:
        """
        Update the rendering view.
        """

        step = copy(self.step)

        # 1. If the group ID changed, change the visibility of Objects
        if self.__group_change:
            self.__group_change = False
            # Remove previous group
            for table_name in self.objects[self.__previous_group].keys():
                v_object = self.get_object(table_name)
                if v_object.type == 'Text':
                    v_object.instance.visible = False
                else:
                    self._scene.scene.remove_geometry(v_object.name)
            # Add new group
            for table_name in self.objects[self.__current_group].keys():
                v_object = self.get_object(table_name)
                if v_object.type == 'Text':
                    v_object.instance.visible = True
                else:
                    self._scene.scene.add_geometry(v_object.name, v_object.instance, v_object.material)

        # 2. Update all the Objects
        if step < max(self.nb_sample.values()):
            self.update_objects(step=step)

    def update_object_backend(self,
                              v_object: Open3dObject) -> None:
        """
        Specific Object update instructions.

        :param v_object: Object object.
        """

        v_object.update()
        if v_object.group == self.__current_group:
            if v_object.type == 'Text':
                pass
            else:
                self._scene.scene.remove_geometry(v_object.name)
                self._scene.scene.add_geometry(v_object.name, v_object.instance, v_object.material)

    def close(self) -> None:
        """
        Exit procedure of the Visualizer.
        """

        self.__is_done = True

    def _change_group(self,
                      index: int) -> None:

        if index != self.__current_group:
            self.__previous_group = self.__current_group
            self.__current_group = index
            self.__group_change = True
