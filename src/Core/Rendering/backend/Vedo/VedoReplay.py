from typing import Dict, Any, Optional
from vedo import show, Plotter

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseReplay import BaseReplay
from SSD.Core.Rendering.backend.Vedo.VedoActor import VedoActor


class VedoReplay(BaseReplay):

    def __init__(self,
                 database: Database,
                 fps: int = 20):

        BaseReplay.__init__(self,
                            database=database,
                            fps=fps)

        # Define the Database
        self.__database = database

        # Information about Actors
        self.__actors: Dict[int, Dict[str, VedoActor]] = {}
        self.__groups: Dict[str, int] = {}

        # Information about the Plotter
        self.__plotter: Optional[Plotter] = None
        self.__nb_sample: Optional[int] = None
        self.__fps: float = 1 / min(max(1, abs(fps)), 50)
        self.__step = 1

    def get_actor(self,
                  actor_name: str) -> VedoActor:
        """
        Get an Actor instance.

        :param actor_name: Name of the Actor.
        """

        group = self.__groups[actor_name]
        return self.__actors[group][actor_name]

    def launch(self) -> None:

        # 1. Sort the Table names per factory and per object indices
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

            # 2.3. Retrieve the good indexing of the Actor
            actor_type = table_name.split('_')[0]
            if group not in self.__actors:
                self.__actors[group] = {}

            # 3.3. Create the Actor
            self.__actors[group][table_name] = VedoActor(actor_type=actor_type,
                                                         actor_name=table_name,
                                                         actor_group=group)
            if actor_type == 'Markers':
                object_data['normal_to'] = self.get_actor(object_data['normal_to'])
            self.__actors[group][table_name].create(data=object_data)
            self.__groups[table_name] = group

        # 3. Create Plotter

        # 3.1. Create the list of actors to render
        actors = []
        for group in sorted(self.__actors.keys()):
            actors.append([])
            for actor in self.__actors[group].values():
                actors[-1].append(actor.instance)

        # 3.2. Create a non_interactive Plotter instance
        self.__plotter = show(actors,
                              new=True,
                              N=len(actors),
                              sharecam=True,
                              interactive=False,
                              title='SSD',
                              axes=4)

        # 3.3. Add a timer callback and set the Plotter in interactive mode
        self.__plotter.add_callback('Timer', self.__update_thread)
        self.__plotter.timer_callback('create', dt=int(self.__fps * 1e3))
        self.__plotter.add_button(self.__start, states=['start'])
        self.__plotter.interactive()

    def __start(self):

        self.__step = 0

    def __update_thread(self, _):

        self.__step += 1
        if self.__step < self.__nb_sample:

            # Retrieve visual data and update Actors (one Table per Actor)
            table_names = self.__database.get_tables()
            for table_name in table_names:

                # Get the full line of data
                object_data = self.__database.get_line(table_name=table_name,
                                                       line_id=self.__step)
                object_data = dict(filter(lambda item: item[1] is not None, object_data.items()))
                object_data.pop('id')

                # Update the Actor and its visualization
                if len(object_data.keys()) > 0 or 'Markers' in table_name:
                    actor = self.get_actor(table_name)
                    # Markers are updated if their associated object was updated
                    if actor.type == 'Markers' and 'normal_to' in object_data.keys():
                        object_data['normal_to'] = self.get_actor(object_data['normal_to'])
                    # Some Actors must be removed from the Plotter to be visually updated
                    removed = False
                    if _do_remove(actor, object_data):
                        self.__plotter.remove(actor.instance, at=actor.group)
                        removed = True
                    # Update Actor
                    actor.update(data=object_data)
                    if removed:
                        self.__plotter.add(actor.instance, at=actor.group)

            # Render the new set of Actors
            self.__plotter.render()


def _do_remove(actor: VedoActor,
               data: Dict[str, Any]) -> bool:

    # Arrows must be re-added to update the vectors
    if actor.type == 'Arrows' and ('positions' in data.keys() or 'vectors' in data.keys()):
        return True

    # Markers must be re-added to update the positions
    elif actor.type == 'Markers' and (len(data) > 0 or 'positions' in actor.object_data['normal_to'].updated_fields):
        return True

    return False
