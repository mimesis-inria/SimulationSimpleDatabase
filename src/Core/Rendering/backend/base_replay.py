from typing import Dict

from SSD.Core.Storage.database import Database
from SSD.Core.Rendering.backend.base_object import BaseObject


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
        self.fps: float = 1 / min(max(1, abs(fps)), 100)
        self.nb_sample: Dict[str, int] = {}
        self.step: int = 1

        # Objects parameters
        self.objects: Dict[int, Dict[str, BaseObject]] = {}
        self.groups: Dict[str, int] = {}

    def get_object(self,
                   object_name: str) -> BaseObject:
        """
        Get an Object instance.

        :param object_name: Name of the Object.
        """

        group = self.groups[object_name]
        return self.objects[group][object_name]

    def start_replay(self) -> None:
        """
        Start the Replay: create all Objects and render them.
        """

        self.create_objects()
        self.launch_visualizer()

    def create_objects(self) -> None:
        """
        Create an Object for each table in the Database.
        """

        # 1. Sort the Table names per factory and per object indices
        table_names = self.database.get_tables(only_names=True)
        sorted_table_names = []
        sorter: Dict[int, Dict[int, str]] = {}
        for table_name in table_names:
            if len(table_name_split := table_name.split('_')) == 3:
                factory_id, table_id = table_name_split[-2:]
                if int(factory_id) not in sorter:
                    sorter[int(factory_id)] = {}
                sorter[int(factory_id)][int(table_id)] = table_name
        for factory_id in sorted(sorter.keys()):
            for table_id in sorted(sorter[factory_id].keys()):
                sorted_table_names.append(sorter[factory_id][table_id])

        # 2. Retrieve visual data and create Objects (one Table per Object)
        for table_name in sorted_table_names:

            # 2.1. Get the number of sample
            self.nb_sample[table_name] = self.database.nb_lines(table_name=table_name)

            # 2.2. Get the full line of data
            object_data = self.database.get_line(table_name=table_name,
                                                 line_id=self.step)
            object_data.pop('id')
            group = object_data.pop('at')

            # 2.3. Retrieve the good indexing of the Object
            object_type = table_name.split('_')[0]
            if group not in self.objects:
                self.objects[group] = {}

            # 2.4. Create the Object
            self.create_object_backend(object_name=table_name,
                                       object_type=object_type,
                                       object_group=group)
            if object_type == 'Markers':
                object_data['normal_to'] = self.get_object(object_data['normal_to'])
            self.objects[group][table_name].create(data=object_data)
            self.groups[table_name] = group

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

        raise NotImplementedError

    def launch_visualizer(self) -> None:
        """
        Start the Visualizer: create all Objects and render them.
        """

        raise NotImplementedError

    def update_objects(self,
                       step: int) -> None:
        """
        Update the Objects of a Factory.

        :param step: Index of the current step.
        """

        for group in self.objects.keys():
            for table_name in self.objects[group].keys():

                # Get the current step line in the Table
                object_data = self.database.get_line(table_name=table_name,
                                                     line_id=step)
                object_data = dict(filter(lambda item: item[1] is not None, object_data.items()))
                object_data.pop('id')

                # Update the Object and its visualization
                if len(object_data.keys()) > 0 or 'Markers' in table_name:
                    v_object = self.get_object(table_name)
                    # Markers are updated if their associated object was updated
                    if v_object.type == 'Markers' and 'normal_to' in object_data.keys():
                        object_data['normal_to'] = self.get_object(object_data['normal_to'])
                    # Update
                    v_object.update_data(data=object_data)
                    self.update_object_backend(v_object=v_object)

    def update_object_backend(self,
                              v_object: BaseObject) -> None:
        """
        Specific Object update instructions.

        :param v_object: Object object.
        """

        raise NotImplementedError

    def reset(self) -> None:
        """
        Reset the step counter.
        """

        self.step = 0
