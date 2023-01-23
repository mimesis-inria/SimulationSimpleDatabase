from typing import Dict
from threading import Thread
from copy import copy
from time import time, sleep
import open3d as o3d

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseReplay import BaseReplay
from SSD.Core.Rendering.backend.Open3d.Open3dBaseApp import BaseApp
from SSD.Core.Rendering.backend.Open3d.Open3dActor import Open3dActor


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

        self.actors: Dict[int, Dict[str, Open3dActor]] = {}
        self.__current_group: int = 0
        self.__previous_group: int = 0
        self.__group_change: bool = False
        self.__is_done = False

    def get_actor(self,
                  actor_name: str) -> Open3dActor:
        """
        Get an Actor instance.

        :param actor_name: Name of the Actor.
        """

        group = self.groups[actor_name]
        return self.actors[group][actor_name]

    def create_actor_backend(self,
                             actor_name: str,
                             actor_type: str,
                             actor_group: int) -> None:
        """
        Specific Actor creation instructions.

        :param actor_name: Name of the Actor.
        :param actor_type: Type of the Actor.
        :param actor_group: Group of the Actor.
        """

        self.actors[actor_group][actor_name] = Open3dActor(actor_type=actor_type,
                                                           actor_name=actor_name,
                                                           actor_group=actor_group)
        if actor_type == 'Text':
            self.additional_labels[actor_name] = self.actors[actor_group][actor_name]

    def launch_visualizer(self) -> None:
        """
        Start the Visualizer: create all Actors and render them.
        """

        # 1. Init Visualizer instance
        self._create_settings(len(self.actors))
        self._window.set_on_close(self.close)

        # 2. Add all Text
        for actor in self.additional_labels.values():
            self._window.add_child(actor.instance)
            actor.instance.visible = False

        # 3. Add geometries to the Visualizer
        for actor in self.actors[self.__current_group].values():
            if actor.type == 'Text':
                actor.instance.visible = True
            else:
                self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)
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

        # 1. If the group ID changed, change the visibility of Actors
        if self.__group_change:
            self.__group_change = False
            # Remove previous group
            for table_name in self.actors[self.__previous_group].keys():
                actor = self.get_actor(table_name)
                if actor.type == 'Text':
                    actor.instance.visible = False
                else:
                    self._scene.scene.remove_geometry(actor.name)
            # Add new group
            for table_name in self.actors[self.__current_group].keys():
                actor = self.get_actor(table_name)
                if actor.type == 'Text':
                    actor.instance.visible = True
                else:
                    self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)

        # 2. Update all the Actors
        if step < self.nb_sample:
            self.update_actors(step=step)

    def update_actor_backend(self,
                             actor: Open3dActor) -> None:
        """
        Specific Actor update instructions.

        :param actor: Actor object.
        """

        actor.update()
        if actor.group == self.__current_group:
            if actor.type == 'Text':
                pass
            else:
                self._scene.scene.remove_geometry(actor.name)
                self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)

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
