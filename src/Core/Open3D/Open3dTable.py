from typing import Any, Dict
from numpy import array, ndarray
from vedo.utils import is_sequence

from SSD.Core.Storage.Database import Database


class Open3dTable:

    def __init__(self,
                 db: Database,
                 table_name: str):

        # Table information
        self.database: Database = db
        self.table_name: str = table_name
        self.table_type: str = table_name.split('_')[0]

        # Select the good methods according to the Table type
        create_columns = {'Mesh': self.__create_mesh_columns,
                          'Points': self.__create_points_columns}
        format_data = {'Mesh': self.__format_mesh_data,
                       'Points': self.__format_points_data}
        self.create_columns = create_columns[self.table_type]
        self.format_data = format_data[self.table_type]

    def send_data(self,
                  data_dict: Dict[str, Any],
                  update: bool):

        if update:
            self.database.update(table_name=self.table_name,
                                 data=self.format_data(data_dict=data_dict))
        else:
            self.database.add_data(table_name=self.table_name,
                                   data=self.format_data(data_dict=data_dict))

    ##################
    # CREATE COLUMNS #
    ##################

    def __create_mesh_columns(self):

        self.database.create_table(table_name=self.table_name,
                                   fields=[('positions', ndarray),
                                           ('cells', ndarray),
                                           ('wireframe', bool),
                                           ('compute_normals', bool),
                                           ('line_width', float),
                                           ('c', str),
                                           ('alpha', float),
                                           ('scalar_field', ndarray),
                                           ('at', int),
                                           ('colormap', str)])
        return self

    def __create_points_columns(self):

        self.database.create_table(table_name=self.table_name,
                                   fields=[('positions', ndarray),
                                           ('point_size', int),
                                           ('c', str),
                                           ('alpha', float),
                                           ('scalar_field', ndarray),
                                           ('at', int),
                                           ('colormap', str)])
        return self

    ###############
    # FORMAT DATA #
    ###############

    @classmethod
    def __format_mesh_data(cls,
                           data_dict: Dict[str, Any]):

        data_dict_copy = data_dict.copy()
        for field, value in data_dict_copy.items():
            if value is None:
                data_dict.pop(field)
            elif field in ['positions', 'cells', 'scalar_field']:
                data_dict[field] = cls.parse_vector(value)
        return data_dict

    @classmethod
    def __format_points_data(cls,
                             data_dict: Dict[str, Any]):

        data_dict_copy = data_dict.copy()
        for field, value in data_dict_copy.items():
            if value is None:
                data_dict.pop(field)
            elif field in ['positions', 'scalar_field']:
                data_dict[field] = cls.parse_vector(value)
        return data_dict

    @classmethod
    def parse_vector(cls,
                     vec: Any):

        if is_sequence(vec):
            if len(vec) > 0 and not is_sequence(vec[0]):
                vec = [vec]
            vec = array(vec)
        return vec
