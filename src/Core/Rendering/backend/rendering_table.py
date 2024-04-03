from typing import Any, Dict
from numpy import array, ndarray
from vedo.utils import is_sequence

from SSD.Core.Storage.database import Database


class RenderingTable:

    def __init__(self,
                 database: Database,
                 table_name: str):
        """
        A RenderingTable is used to create a specific Table in the Database for each object type.
        
        :param database: Database to connect to.
        :param table_name: Name of the Table to create. Should be '<obj_type>_<factory_idx>_<obj_idx>'.
        """

        # Table information
        self.database: Database = database
        self.table_name: str = table_name
        self.table_type: str = table_name.split('_')[0]

    def send_data(self,
                  data: Dict[str, Any],
                  update: bool) -> None:
        """
        Create a new line in the Table or update the last one.

        :param data: Data to send to the Database.
        :param update: If False, create a new line in the Table.
        """

        # Update the current line of the Table
        if update:
            self.database.update(table_name=self.table_name,
                                 data=self.__format_data(data=data))
        # Create a new line in the Table
        else:
            self.database.add_data(table_name=self.table_name,
                                   data=self.__format_data(data=data))

    def create_columns(self) -> 'RenderingTable':
        """
        Create the Fields of the Table for a specific object type.
        """

        return {'Mesh': self.__create_mesh_columns,
                'Points': self.__create_points_columns,
                'Arrows': self.__create_arrows_columns,
                'Markers': self.__create_markers_columns,
                'Text': self.__create_text_columns
                }[self.table_type]()

    def __create_mesh_columns(self) -> 'RenderingTable':

        self.database.create_table(table_name=self.table_name,
                                   fields=[('positions', ndarray),
                                           ('cells', ndarray),
                                           ('wireframe', bool),
                                           ('line_width', float),
                                           ('c', str),
                                           ('alpha', float),
                                           ('scalar_field', ndarray),
                                           ('at', int),
                                           ('colormap', str)
                                           ])
        return self

    def __create_points_columns(self) -> 'RenderingTable':

        self.database.create_table(table_name=self.table_name,
                                   fields=[('positions', ndarray),
                                           ('point_size', int),
                                           ('c', str),
                                           ('alpha', float),
                                           ('scalar_field', ndarray),
                                           ('at', int),
                                           ('colormap', str)
                                           ])
        return self

    def __create_arrows_columns(self) -> 'RenderingTable':

        self.database.create_table(table_name=self.table_name,
                                   fields=[('positions', ndarray),
                                           ('vectors', ndarray),
                                           ('res', int),
                                           ('c', str),
                                           ('alpha', float),
                                           ('scalar_field', ndarray),
                                           ('at', int),
                                           ('colormap', str)
                                           ])
        return self

    def __create_markers_columns(self) -> 'RenderingTable':

        self.database.create_table(table_name=self.table_name,
                                   fields=[('normal_to', str),
                                           ('indices', ndarray),
                                           ('symbol', str),
                                           ('size', float),
                                           ('filled', bool),
                                           ('c', str),
                                           ('alpha', float),
                                           ('scalar_field', ndarray),
                                           ('at', int),
                                           ('colormap', str)
                                           ])
        return self

    def __create_text_columns(self) -> 'RenderingTable':

        self.database.create_table(table_name=self.table_name,
                                   fields=[('content', str),
                                           ('corner', str),
                                           ('c', str),
                                           ('font', str),
                                           ('size', int),
                                           ('bold', bool),
                                           ('italic', bool),
                                           ('at', int)
                                           ])
        return self

    @classmethod
    def __format_data(cls,
                      data: Dict[str, Any]) -> Dict[str, Any]:

        data_copy = data.copy()
        for field, value in data_copy.items():
            if value is None:
                data.pop(field)
            elif field in ['positions', 'cells', 'scalar_field', 'vectors', 'indices']:
                data[field] = cls.__parse_vector(value)
        return data

    @classmethod
    def __parse_vector(cls,
                       vec: Any) -> ndarray:

        if is_sequence(vec):
            if len(vec) > 0 and not is_sequence(vec[0]):
                vec = [vec]
            vec = array(vec)
        return vec
