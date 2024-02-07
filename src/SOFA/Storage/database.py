from typing import Any, Dict, Tuple
import Sofa

from SSD.Core.Storage.database import Database as CoreDatabase
from SSD.SOFA.utils import error_message


class Database(Sofa.Core.Controller, CoreDatabase):

    def __init__(self,
                 root: Sofa.Core.Node,
                 database_dir: str = '',
                 database_name: str = 'runSofa',
                 *args, **kwargs):
        """
        Manage the creation and loading of Tables in the Database.
        User interface to dynamically add, get and update entries.
        Additional callbacks to automatically get SOFA objects Data.

        :param root: Root node of the scene graph.
        :param database_dir: Directory which contains the Database file.
        :param database_name: Name of the Database file.
        """

        Sofa.Core.Controller.__init__(self, *args, **kwargs)
        CoreDatabase.__init__(self,
                              database_dir=database_dir,
                              database_name=database_name)

        # Add the Database controller to the scene graph
        self.root: Sofa.Core.Node = root
        self.root.addChild('database')
        self.root.database.addObject(self)

        self.__callbacks: Dict[str, Dict[str, Tuple[Sofa.Core.Object, str]]] = {}
        self.__dirty: Dict[str, bool] = {}
        self.__path: Dict[str, Dict[str, str]] = {}

    def add_callback(self,
                     table_name: str,
                     field_name: str,
                     record_object: str,
                     record_field: str):
        """
        Add a callback on an object Data field. If the specified Table or Field does not exist, create them.

        :param table_name: Name of the Table.
        :param field_name: Name of the Field.
        :param record_object: Path to the SOFA object in the scene graph from root node ('@child_node.object_name').
        :param record_field: The name of the Data field to record.
        """

        # Check Table existence
        table_name = self.make_name(table_name)
        if table_name not in self.get_tables():
            self.create_table(table_name=table_name)

        # Check the path
        if record_object[0] != '@' or len(record_object[1:].split('.')) == 0:
            error_message(f"You must give the absolute path to the object to record. "
                          f"The path '{record_object}' must be defined such as '@child_node.object_name'.")

        # Access each child node
        node: Sofa.Core.Node = self.root
        child_nodes = record_object[1:].split('.')[:-1]
        if len(child_nodes) > 0 and child_nodes[0] == node.getName():
            child_nodes.pop(0)
        for child_node in child_nodes:
            if child_node not in node.children:
                node_path = f'{self.root.getName()}{node.getPathName()}'
                error_message(f"The node '{child_node}' is not a child of '{node_path}'. "
                              f"Available children are {[n.getName() for n in node.children]}.")
            node = node.getChild(child_node)

        # Access object
        object_name = record_object[1:].split('.')[-1]
        if object_name not in node.objects:
            node_path = f'{self.root.getName()}{node.getPathName()}'
            error_message(f"The object '{object_name} does not belong to node '{node_path}'. "
                          f"Available objects are {[o.getName() for o in node.objects]}.")
        obj: Sofa.Core.Object = node.getObject(object_name)

        # Check Data access and get Data type
        if (data := obj.getData(record_field)) is None:
            error_message(f"The object {obj.getName()} does not have a '{field_name}' Data field.")
        data_type = type(data.value)

        # Check Field existence
        if field_name not in self.get_fields(table_name=table_name):
            self.create_fields(table_name=table_name,
                               fields=(field_name, data_type))

        # Register the object
        if table_name not in self.__callbacks:
            self.__callbacks[table_name] = {}
            self.__path[table_name] = {}
        if field_name in self.__callbacks[table_name]:
            error_message(f"The Field '{field_name}' in Table '{table_name}' is already associated with an object.")
        self.__callbacks[table_name][field_name] = (obj, record_field)
        self.__path[table_name][field_name] = f'@root.{record_object[1:]}.{record_field}'

    def onAnimateBeginEvent(self, _):
        """
        At the beginning of a time step.
        """

        # Reset all the dirty flags
        self.__dirty = {table: False for table in self.get_tables()}

    def onAnimateEndEvent(self, _):
        """
        At the end of a time step.
        """

        # Execute all callbacks
        for table_name in self.__callbacks:
            data = {}
            for field_name, (record_object, record_field) in self.__callbacks[table_name].items():
                data[field_name] = record_object.getData(record_field).value
            self.add_data(table_name=table_name, data=data)

        # If a Table was not updated, add an empty line (keep one line per time step)
        for table_name, dirty in self.__dirty.items():
            if not dirty:
                self.add_data(table_name, data={})

    def add_data(self,
                 table_name: str,
                 data: Dict[str, Any]):
        """
        Execute a line insert query.

        :param table_name: Name of the Table.
        :param data: New line of the Table.
        """

        table_name = self.make_name(table_name)
        # If the Table was already edited during the time then update it (keep one line per time step)
        if self.__dirty[table_name]:
            self.update(table_name=table_name, data=data)
        # Otherwise, create a new line
        else:
            self.__dirty[table_name] = True
            CoreDatabase.add_data(self, table_name=table_name, data=data)

    def print_architecture(self):
        """
        Print the content of the Database with Table(s), Field(s) and connected SOFA objects.
        """

        print(f'\nDATABASE {self.__database_name}.db')
        for name, table in self.get_tables(only_names=False).items():
            info = table.description(indent=True, name=name).split('\n')
            for i, line in enumerate(info[1:-1]):
                field_name = line.split('-')[1].split(' ')[1]
                if name in self.__callbacks:
                    if field_name in self.__callbacks[name]:
                        info[i + 1] = line + f' --> {self.__path[name][field_name]}'
            for i in range(len(info) - 2):
                info[i] += '\n'
            print(''.join(info))
        print('')
