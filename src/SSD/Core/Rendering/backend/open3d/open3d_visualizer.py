import socket
from typing import Dict, Optional, Tuple
from threading import Thread
from struct import unpack
from copy import copy
from time import time, sleep
import open3d.visualization.gui as gui

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.backend.base_visualizer import BaseVisualizer
from SSD.Core.Rendering.backend.open3d.open3d_object import Open3dObject
from SSD.Core.Rendering.backend.open3d.open3d_app import BaseApp


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

        self.objects: Dict[int, Dict[str, Open3dObject]] = {}
        self.__current_group: int = 0
        self.__previous_group: int = 0
        self.__group_change: bool = False
        self.__step: Tuple[int, int] = (1, 1)

    def get_object(self,
                   object_name: str) -> Open3dObject:
        """
        Get an Actor instance.

        :param object_name: Name of the Actor.
        """

        group = self.groups[object_name]
        return self.objects[group][object_name]

    def create_object_backend(self,
                              object_name: str,
                              object_type: str,
                              object_group: int) -> None:
        """
        Specific Actor creation instructions.

        :param object_name: Name of the Actor.
        :param object_type: Type of the Actor.
        :param object_group: Group of the Actor.
        """

        self.objects[object_group][object_name] = Open3dObject(object_type=object_type,
                                                               object_name=object_name,
                                                               object_group=object_group)
        if object_type == 'Text':
            self.additional_labels[object_name] = self.objects[object_group][object_name]

    def launch_visualizer(self,
                          nb_clients: int) -> None:
        """
        Start the Visualizer: create all Actors and render them.

        :param nb_clients: Number of Factories to connect to.
        """

        # 1. Init Visualizer instance
        self._create_settings(len(self.objects))
        self._window.set_on_close(self.exit)

        # 2 Add all Text
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
            try:
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
            except socket.timeout:
                pass

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
            for table_name in self.objects[self.__previous_group].keys():
                v_object: Open3dObject = self.get_object(table_name)
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

        # 2. Update all the Actors
        self.update_objects(step=step,
                            idx_factory=idx_factory)
        self.clients[idx_factory].send(b'done')

    def update_object_backend(self,
                              v_object: Open3dObject) -> None:
        """
        Specific Actor update instructions.

        :param v_object: Actor object.
        """

        v_object.update()
        if v_object.group == self.__current_group:
            if v_object.type == 'Text':
                pass
            else:
                self._scene.scene.remove_geometry(v_object.name)
                self._scene.scene.add_geometry(v_object.name, v_object.instance, v_object.material)

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
