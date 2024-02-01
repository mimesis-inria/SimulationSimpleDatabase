import socket
from typing import Dict, Optional
from struct import unpack
from vedo import show, Plotter
from threading import Thread

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.backend.base_visualizer import BaseVisualizer
from SSD.Core.Rendering.backend.vedo.vedo_objet import VedoObject
from SSD.Core.Rendering.backend.vedo.utils import do_remove


class VedoVisualizer(BaseVisualizer):

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 fps: int = 20):
        """
        The VedoVisualizer is used to manage the creation, update and rendering of Vedo Objects.

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

        self.objects: Dict[int, Dict[str, VedoObject]] = {}
        self.__plotter: Optional[Plotter] = None

    def get_object(self,
                   object_name: str) -> VedoObject:
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

        self.objects[object_group][object_name] = VedoObject(object_type=object_type,
                                                             object_name=object_name,
                                                             object_group=object_group)

    def launch_visualizer(self,
                          nb_clients: int) -> None:
        """
        Start the Visualizer: create all Objects and render them.

        :param nb_clients: Number of Factories to connect to.
        """

        # 1. Create the list of objects to render
        objects = []
        for group in self.objects.keys():
            objects.append([])
            for v_object in self.objects[group].values():
                objects[-1].append(v_object.instance)

        # 2. Create a non-interactive Plotter instance
        self.__plotter = show(objects,
                              new=True,
                              N=len(objects),
                              sharecam=True,
                              interactive=False,
                              title='SSD',
                              axes=4)

        # 3. Add a timer callback and set the Plotter in interactive mode
        timer_id = self.__plotter.timer_callback('create', dt=int(self.fps * 1e3) // nb_clients)
        if nb_clients == 1:
            self.__plotter.add_callback('timer', self.single_client_thread)
            self.clients[0].send(b'done')
        else:
            self.__plotter.add_callback('timer', self.multiple_clients_thread)
            for i, client in enumerate(self.clients):
                client.send(b'done')
                Thread(target=self.listen_client, args=(i,)).start()
        self.__plotter.interactive()
        self.__plotter.timer_callback('destroy', timer_id=timer_id)
        self.__plotter.close()
        self.__plotter = None

        # 4. The window was closed
        if False in self.is_done:
            self.exit()

    def single_client_thread(self, _) -> None:
        """
        Timer callback for a single Factory.
        """

        try:
            msg = self.clients[0].recv(4)
            if len(msg) == 0:
                pass
            elif msg == b'exit':
                self.is_done[0] = True
                self.exit(force_quit=False)
            else:
                step = unpack('i', msg)[0]
                self.update_visualizer(step=step, idx_factory=0)
                self.clients[0].send(b'done')
        except socket.timeout:
            pass

    def multiple_clients_thread(self, _) -> None:
        """
        Timer callback for several Factories.
        """

        if len(self.requests) > 0:
            i, step = self.requests.pop(0)
            self.update_visualizer(step=step, idx_factory=i)
            self.clients[i].send(b'done')

    def update_visualizer(self,
                          step: int,
                          idx_factory: int) -> None:
        """
        Update the rendering view.

        :param step: Index of the current step.
        :param idx_factory: Index of the Factory to update.
        """

        self.update_objects(step=step,
                            idx_factory=idx_factory)
        self.__plotter.render()

    def update_object_backend(self,
                              v_object: VedoObject) -> None:
        """
        Specific Object update instructions.

        :param v_object: Object object.
        """

        removed = False
        if do_remove(v_object, v_object.updated_fields):
            self.__plotter.remove(v_object.instance, at=v_object.group)
            removed = True
        v_object.update()
        if removed:
            self.__plotter.add(v_object.instance, at=v_object.group)

    def exit(self,
             force_quit: bool = True) -> None:
        """
        Exit procedure of the Visualizer.

        :param force_quit: True if the Window was manually closed.
        """

        if force_quit:
            for i, client in enumerate(self.clients):
                client.send(b'exit')

        # Close the socket
        if self.server is not None:
            self.server.close()
            self.server = None

        # Close the Plotter
        if self.__plotter is not None:
            self.__plotter.break_interaction()
