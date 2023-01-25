from typing import Dict, Optional
from vedo import show, Plotter

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseReplay import BaseReplay
from SSD.Core.Rendering.backend.Vedo.VedoActor import VedoActor
from SSD.Core.Rendering.backend.Vedo.utils import do_remove


class VedoReplay(BaseReplay):

    def __init__(self,
                 database: Database,
                 fps: int = 20):
        """
        Replay a simulation from saved visual data with Vedo.

        :param database: Database to connect to.
        :param fps: Max frame rate.
        """

        BaseReplay.__init__(self,
                            database=database,
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

    def launch_visualizer(self) -> None:
        """
        Start the Visualizer: create all Actors and render them.
        """

        # 1. Create the list of actors to render
        actors = []
        for group in sorted(self.actors.keys()):
            actors.append([])
            for actor in self.actors[group].values():
                actors[-1].append(actor.instance)

        # 2. Create a non_interactive Plotter instance
        self.__plotter = show(actors,
                              new=True,
                              N=len(actors),
                              sharecam=True,
                              interactive=False,
                              title='SSD',
                              axes=4)

        # 3. Add a timer callback and set the Plotter in interactive mode
        self.__plotter.add_callback('Timer', self.update_thread)
        self.__plotter.timer_callback('create', dt=int(self.fps * 1e3))
        self.__plotter.add_button(self.reset, states=['start'])
        self.__plotter.interactive()

    def update_thread(self, _):
        """
        Timer callback to update the rendering view.
        """

        self.step += 1
        if self.step < max(self.nb_sample.values()):
            self.update_actors(step=self.step)
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
