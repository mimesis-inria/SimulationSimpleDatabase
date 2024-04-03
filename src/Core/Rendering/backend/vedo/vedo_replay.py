from typing import Dict, Optional
from vedo import show, Plotter

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.backend.base_replay import BaseReplay
from SSD.Core.Rendering.backend.vedo.vedo_objet import VedoObject
from SSD.Core.Rendering.backend.vedo.utils import do_remove


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

    def launch_visualizer(self) -> None:
        """
        Start the Visualizer: create all Objects and render them.
        """

        # 1. Create the list of objects to render
        objects = []
        for group in sorted(self.objects.keys()):
            objects.append([])
            for v_object in self.objects[group].values():
                objects[-1].append(v_object.instance)

        # 2. Create a non_interactive Plotter instance
        self.__plotter = show(objects,
                              new=True,
                              N=len(objects),
                              sharecam=True,
                              interactive=False,
                              title='SSD',
                              axes=4)

        # 3. Add a timer callback and set the Plotter in interactive mode
        self.__plotter.add_callback('Timer', self.update_thread, enable_picking=False)
        self.__plotter.timer_callback('create', dt=int(self.fps * 1e3))
        self.__plotter.add_button(self.__reset, states=['start'])
        self.__plotter.interactive()

    def update_thread(self, _):
        """
        Timer callback to update the rendering view.
        """

        self.step += 1
        if self.step < max(self.nb_sample.values()):
            self.update_objects(step=self.step)
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

    def __reset(self, obj, name):

        self.reset()
