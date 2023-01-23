from typing import Optional, Dict

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseActor import BaseActor


class BaseReplay:

    def __init__(self,
                 database: Database,
                 fps: int = 20):
        """
        The BaseReplay is the common API for all backend Replays.

        :param database: Database to connect to.
        :param fps: Max frame rate.
        """

        # Define the Database
        self.database = database

        # Visualization parameters
        self.fps: float = 1 / min(max(1, abs(fps)), 50)
        self.nb_sample: Optional[int] = None
        self.step: int = 1

        # Actors parameters
        self.actors: Dict[int, Dict[str, BaseActor]] = {}
        self.groups: Dict[str, int] = {}

    def get_actor(self,
                  actor_name: str) -> BaseActor:
        """
        Get an Actor instance.

        :param actor_name: Name of the Actor.
        """

        group = self.groups[actor_name]
        return self.actors[group][actor_name]

    def start_replay(self) -> None:
        """
        Start the Replay: create all Actors and render them.
        """

        self.create_actors()
        self.launch_visualizer()

    def create_actors(self) -> None:
        """
        Create an Actor object for each table in the Database.
        """

        # 1. Sort the Table names per factory and per object indices
        table_names = self.database.get_tables()
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
            self.nb_sample = self.database.nb_lines(table_name=table_name)

            # 2.2. Get the full line of data
            object_data = self.database.get_line(table_name=table_name,
                                                 line_id=self.step)
            object_data.pop('id')
            group = object_data.pop('at')

            # 2.3. Retrieve the good indexing of the Actor
            actor_type = table_name.split('_')[0]
            if group not in self.actors:
                self.actors[group] = {}

            # 2.4. Create the Actor
            self.create_actor_backend(actor_name=table_name,
                                      actor_type=actor_type,
                                      actor_group=group)
            if actor_type == 'Markers':
                object_data['normal_to'] = self.get_actor(object_data['normal_to'])
            self.actors[group][table_name].create(data=object_data)
            self.groups[table_name] = group

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

        raise NotImplementedError

    def launch_visualizer(self) -> None:
        """
        Start the Visualizer: create all Actors and render them.
        """

        raise NotImplementedError

    def update_actors(self,
                      step: int) -> None:
        """
        Update the Actors of a Factory.

        :param step: Index of the current step.
        """

        for group in self.actors.keys():
            for table_name in self.actors[group].keys():

                # Get the current step line in the Table
                object_data = self.database.get_line(table_name=table_name,
                                                     line_id=step)
                object_data = dict(filter(lambda item: item[1] is not None, object_data.items()))
                object_data.pop('id')

                # Update the Actor and its visualization
                if len(object_data.keys()) > 0 or 'Markers' in table_name:
                    actor = self.get_actor(table_name)
                    # Markers are updated if their associated object was updated
                    if actor.type == 'Markers' and 'normal_to' in object_data.keys():
                        object_data['normal_to'] = self.get_actor(object_data['normal_to'])
                    # Update
                    actor.update_data(data=object_data)
                    self.update_actor_backend(actor=actor)

    def update_actor_backend(self,
                             actor: BaseActor) -> None:
        """
        Specific Actor update instructions.

        :param actor: Actor object.
        """

        raise NotImplementedError

    def reset(self) -> None:
        """
        Reset the step counter.
        """

        self.step = 0
