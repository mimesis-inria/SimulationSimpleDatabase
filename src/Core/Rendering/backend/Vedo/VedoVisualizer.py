import socket
from typing import Dict, Optional
from struct import unpack
from vedo import show, Plotter
from threading import Thread

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseVisualizer import BaseVisualizer
from SSD.Core.Rendering.backend.Vedo.VedoActor import VedoActor
from SSD.Core.Rendering.backend.Vedo.utils import do_remove


class VedoVisualizer(BaseVisualizer):

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 fps: int = 20):
        """
        The VedoVisualizer is used to manage the creation, update and rendering of Vedo Actors.

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

        self.actors: Dict[int, Dict[str, VedoActor]] = {}
        self.__plotter: Optional[Plotter] = None

    def get_actor(self,
                  actor_name: str) -> VedoActor:
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

        self.actors[actor_group][actor_name] = VedoActor(actor_type=actor_type,
                                                         actor_name=actor_name,
                                                         actor_group=actor_group)

    def launch_visualizer(self,
                          nb_clients: int) -> None:
        """
        Start the Visualizer: create all Actors and render them.

        :param nb_clients: Number of Factories to connect to.
        """

        # 1. Create the list of actors to render
        actors = []
        for group in self.actors.keys():
            actors.append([])
            for actor in self.actors[group].values():
                actors[-1].append(actor.instance)

        # 2. Create a non-interactive Plotter instance
        self.__plotter = show(actors,
                              new=True,
                              N=len(actors),
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

        self.update_actors(step=step,
                           idx_factory=idx_factory)
        self.__plotter.render()

    def update_actor_backend(self,
                             actor: VedoActor) -> None:
        """
        Specific Actor update instructions.

        :param actor: Actor object.
        """

        removed = False
        if do_remove(actor, actor.updated_fields):
            self.__plotter.remove(actor.instance, at=actor.group)
            removed = True
        actor.update()
        if removed:
            self.__plotter.add(actor.instance, at=actor.group)

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
