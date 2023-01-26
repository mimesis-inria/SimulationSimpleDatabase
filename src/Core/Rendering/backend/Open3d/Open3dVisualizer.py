from typing import Dict, Optional, Tuple
from threading import Thread
from struct import unpack
from copy import copy
from time import time, sleep
import open3d.visualization.gui as gui

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseVisualizer import BaseVisualizer
from SSD.Core.Rendering.backend.Open3d.Open3dActor import Open3dActor
from SSD.Core.Rendering.backend.Open3d.Open3dBaseApp import BaseApp


class Open3dVisualizer(BaseApp, BaseVisualizer):

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 fps: int = 20):
        """
        The Open3dVisualizer is used to manage the creation, update and rendering of Open3D Actors.

        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param fps: Max frame rate.
        """

        BaseVisualizer.__init__(self,
                                database=database,
                                database_dir=database_dir,
                                database_name=database_name,
                                remove_existing=remove_existing,
                                fps=fps)

        self.actors: Dict[int, Dict[str, Open3dActor]] = {}
        self.__current_group: int = 0
        self.__previous_group: int = 0
        self.__group_change: bool = False
        self.__step: Tuple[int, int] = (1, 1)

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

    def launch_visualizer(self,
                          nb_clients: int) -> None:
        """
        Start the Visualizer: create all Actors and render them.

        :param nb_clients: Number of Factories to connect to.
        """

        # 1. Init Visualizer instance
        self._create_settings(len(self.actors))
        self._window.set_on_close(self.exit)

        # 2 Add all Text
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

        # 4. Launch mainloop
        if nb_clients == 1:
            Thread(target=self.single_client_thread).start()
            self.clients[0].send(b'done')
        else:
            for i, client in enumerate(self.clients):
                Thread(target=self.listen_client, args=(i,)).start()
                client.send(b'done')
            Thread(target=self.multiple_clients_thread).start()

        gui.Application.instance.run()

    def single_client_thread(self):
        """
        Timer callback for a single Factory.
        """

        while not self.is_done[0]:

            msg = self.clients[0].recv(4)
            if len(msg) == 0:
                pass
            elif msg == b'exit':
                self.is_done[0] = True
                self.exit(force_quit=False)
            else:
                self.__step = (0, unpack('i', msg)[0])
                process_time = time()
                gui.Application.instance.post_to_main_thread(self._window,
                                                             self.update_visualizer)
                dt = max(0., self.fps - (time() - process_time))
                sleep(dt)

        gui.Application.instance.quit()

    def multiple_clients_thread(self) -> None:
        """
        Timer callback for several Factories.
        """

        while False in self.is_done:

            if len(self.requests) > 0:
                self.__step = self.requests.pop(0)
                process_time = time()
                gui.Application.instance.post_to_main_thread(self._window,
                                                             self.update_visualizer)
                dt = max(0., self.fps - (time() - process_time))
                sleep(dt)

        gui.Application.instance.quit()

    def update_visualizer(self) -> None:
        """
        Update the rendering view.
        """

        idx_factory, step = copy(self.__step)

        # 1. If the group ID changed, change the visibility of Actors
        if self.__group_change:
            self.__group_change = False
            # Remove previous group
            for table_name in self.actors[self.__previous_group].keys():
                actor: Open3dActor = self.get_actor(table_name)
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
        self.update_actors(step=step,
                           idx_factory=idx_factory)
        self.clients[idx_factory].send(b'done')

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

    def exit(self,
             force_quit: bool = True) -> None:
        """
        Exit procedure of the Visualizer.

        :param force_quit: True if the Window was manually closed.
        """

        if force_quit:
            for i, client in enumerate(self.clients):
                client.send(b'exit')
                self.is_done[i] = True

        # Close the socket
        if self.server is not None:
            self.server.close()
            self.server = None

    def _change_group(self,
                      index: int) -> None:

        if index != self.__current_group:
            self.__previous_group = self.__current_group
            self.__current_group = index
            self.__group_change = True
