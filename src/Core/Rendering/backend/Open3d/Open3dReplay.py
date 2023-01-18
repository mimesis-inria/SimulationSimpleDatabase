from typing import Dict, Optional
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

        BaseReplay.__init__(self,
                            database=database,
                            fps=fps)

        # Define the Database
        self.__database = database

        # Information about Actors
        self.__actors: Dict[int, Dict[str, Open3dActor]] = {}
        self.__groups: Dict[str, int] = {}
        self.__current_group: int = 0
        self.__previous_group: int = 0
        self.__group_change: bool = False

        # Information about the Plotter
        self.__fps: float = 1 / min(max(1, abs(fps)), 50)
        self.__nb_sample: Optional[int] = None
        self.__step: int = 1
        self.__is_done = False

    def get_actor(self,
                  actor_name: str) -> Open3dActor:
        """
        Get an Actor instance.

        :param actor_name: Name of the Actor.
        """

        group = self.__groups[actor_name]
        return self.__actors[group][actor_name]

    def launch(self) -> None:

        # 1. Sort the Tables names per factory and per object indices
        table_names = self.__database.get_tables()
        sorted_table_names = []
        sorter: Dict[int, Dict[int, str]] = {}
        for table_name in table_names:
            factory_id, table_id = table_name.split('_')[-2:]
            if int(factory_id) not in sorter:
                sorter[int(factory_id)] = {}
            sorter[int(factory_id)][int(table_id)] = table_name
        for factory_id in sorted(sorter.keys()):
            for table_id in sorted(sorter[factory_id].keys()):
                sorted_table_names.append(sorter[factory_id][table_id])

        # 2. Retrieve visual data and create Actors (one Table per Actor)
        for table_name in sorted_table_names:

            # 2.1. Get the number of sample
            self.__nb_sample = self.__database.nb_lines(table_name=table_name)

            # 2.2. Get the full line of data
            object_data = self.__database.get_line(table_name=table_name,
                                                   line_id=self.__step)
            object_data.pop('id')
            group = object_data.pop('at')

            # 2.3. Retrieve the good indexing of Actors
            actor_type = table_name.split('_')[0]
            if group not in self.__actors:
                self.__actors[group] = {}

            # 2.4. Create the Actor
            self.__actors[group][table_name] = Open3dActor(actor_type=actor_type,
                                                           actor_name=table_name,
                                                           actor_group=group)
            if actor_type == 'Markers':
                object_data['normal_to'] = self.get_actor(object_data['normal_to'])
            elif actor_type == 'Text':
                self.additional_labels[table_name] = self.__actors[group][table_name]
            self.__actors[group][table_name].create(data=object_data)
            self.__groups[table_name] = group

        # 3. Create Visualizer

        # 3.1. Init Visualizer instance
        self._create_settings(len(self.__actors))
        self._window.set_on_close(self._exit)

        # 3.2 Add all Text
        for actor in self.additional_labels.values():
            self._window.add_child(actor.instance)
            actor.instance.visible = False

        # 3.3. Add geometries to the Visualizer
        for actor in self.__actors[self.__current_group].values():
            if actor.type == 'Text':
                actor.instance.visible = True
            else:
                self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)
        bounds = self._scene.scene.bounding_box
        self._scene.setup_camera(60, bounds, bounds.get_center())

        # 3.4. Add Start button
        bu = o3d.visualization.gui.Button('Start')
        bu.set_on_clicked(self.__start)
        separation_height = int(round(self._window.theme.font_size * 0.5))
        self._settings_panel.add_fixed(2 * separation_height)
        self._settings_panel.add_child(bu)

        # 3.5. Launch mainloop
        Thread(target=self.__update_thread).start()
        o3d.visualization.gui.Application.instance.run()

    def __update_thread(self) -> None:

        while not self.__is_done:
            self.__step += 1
            process_time = time()
            o3d.visualization.gui.Application.instance.post_to_main_thread(self._window,
                                                                           self.__update_instances)
            # Respect frame rate
            dt = max(0., self.__fps - (time() - process_time))
            sleep(dt)

        # Close the Visualizer
        o3d.visualization.gui.Application.instance.quit()

    def __update_instances(self) -> None:

        step = copy(self.__step)

        # 1. If the group ID changed, change the visibility of Actors
        if self.__group_change:
            self.__group_change = False
            # Remove previous group
            for table_name in self.__actors[self.__previous_group].keys():
                actor = self.get_actor(table_name)
                if actor.type == 'Text':
                    actor.instance.visible = False
                else:
                    self._scene.scene.remove_geometry(actor.name)
            # Add new group
            for table_name in self.__actors[self.__current_group].keys():
                actor = self.get_actor(table_name)
                if actor.type == 'Text':
                    actor.instance.visible = True
                else:
                    self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)

        # 2. Update all the Actors
        if step < self.__nb_sample:
            for group_id in self.__actors.keys():
                for table_name in self.__actors[group_id].keys():

                    # 2.1. Get the current step line in the Table
                    object_data = self.__database.get_line(table_name=table_name,
                                                           line_id=step)
                    object_data = dict(filter(lambda item: item[1] is not None, object_data.items()))

                    # 2.2. If the line contains fields, the Actor was updated, then update it
                    object_data.pop('id')
                    if len(object_data.keys()) > 0 or 'Markers' in table_name:
                        # Update Actor instance
                        actor = self.get_actor(table_name)
                        if actor.type == 'Markers' and 'normal_to' in object_data.keys():
                            object_data['normal_to'] = self.get_actor(object_data['normal_to'])
                        actor.update(data=object_data)
                        # Update the geometry in the Visualizer
                        if group_id == self.__current_group:
                            if actor.type == 'Text':
                                pass
                            else:
                                self._scene.scene.remove_geometry(actor.name)
                                self._scene.scene.add_geometry(actor.name, actor.instance, actor.material)

    def _exit(self) -> None:

        # Tell the Plotter to stop
        self.__is_done = True

    def _change_group(self,
                      index: int) -> None:

        if index != self.__current_group:
            self.__previous_group = self.__current_group
            self.__current_group = index
            self.__group_change = True

    def __start(self):

        self.__step = 0
