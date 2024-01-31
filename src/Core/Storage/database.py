from typing import Union, List, Type, Dict, Tuple, Optional, Any, Callable
from os import remove, mkdir
from os.path import exists, join, sep, getsize
from inspect import getmembers
from peewee import ForeignKeyField
from playhouse.migrate import SqliteDatabase
from playhouse.signals import Signal, pre_save, post_save
from datetime import datetime
from numpy import unique

from SSD.Core.Storage.adaptive_table import AdaptiveTable, StoringTable, ExchangeTable
from SSD.Core.Storage.peewee_extension import generate_models
from SSD.Core.Storage.exporter import Exporter

FieldType = Union[Tuple[str, Type], Tuple[str, Type, Any], Tuple[str, str]]


class Database:

    def __init__(self,
                 database_dir: str = '',
                 database_name: str = 'database'):
        """
        Manage the creation and loading of Tables in the Database.
        User interface to dynamically add, get and update entries.
        
        :param database_dir: Directory which contains the Database file.
        :param database_name: Name of the Database file.
        """

        # Eventually remove extension from the database name
        database_name = database_name if len(database_name.split('.')) == 1 else database_name.split('.')[0]

        self.__database_dir = database_dir
        self.__database_name = database_name
        self.__database: Optional[SqliteDatabase] = None
        self.__tables: Dict[str, type(AdaptiveTable)] = {}
        self.__fk: Dict[str, Dict[str, str]] = {}
        self.__signals: List[Tuple[str, Signal, str, Callable, str]] = []

    @staticmethod
    def make_name(table_name: str) -> str:
        """
        Harmonize the Table names.

        :param table_name: Name of the Table.
        """

        return table_name[0] + table_name[1:].lower() if len(table_name) > 1 else table_name

    def new(self, remove_existing: bool = False) -> 'Database':
        """
        Create a new Database file.

        :param remove_existing: If True, Database file will be overwritten.
        """

        # Create directory if not exists
        if not exists(self.__database_dir) and self.__database_dir != '':
            mkdir(self.__database_dir)

        # Check for existing similar files
        if exists(database_path := join(self.__database_dir, f'{self.__database_name}.db')):
            # Option 1: Overwriting file
            if remove_existing:
                remove(database_path)
            # Option 2: Indexing file name
            else:
                index = 1
                while exists(database_path := join(self.__database_dir, f'{self.__database_name}({index}).db')):
                    index += 1
                self.__database_name = f'{self.__database_name}({index})'

        # Create the Database
        self.__database = SqliteDatabase(database_path)
        return self

    def load(self, show_architecture: bool = False) -> 'Database':
        """
        Load an existing Database file.

        :param show_architecture: If True, the loaded models will be printed.
        """

        # Check file existence
        if not exists(database_path := join(self.__database_dir, f'{self.__database_name}.db')):
            raise ValueError(f"WARNING: the following Database does not exist ({database_path}).")

        # Load the Database
        self.__database = SqliteDatabase(database_path)
        models, database_descr = generate_models(self.__database)
        for table_name, model in models.items():
            # Loading removes the '_' symbol in desc.model_names
            table_name_parts = table_name.split('_')
            loaded_name = database_descr.model_names[table_name]
            real_name = ''
            for i, table_name_part in enumerate(table_name_parts):
                real_name += loaded_name[:len(table_name_part)] if i == 0 else f'_{loaded_name[:len(table_name_part)]}'
                loaded_name = loaded_name[len(table_name_part):]
            # Register name
            table_name = self.make_name(real_name)
            self.__tables[table_name] = model
            self.__tables[table_name]._meta.name = table_name

        # Register FK
        for table_name in self.__tables:
            self.__fk[table_name] = {}
            for field_name, field in self.__tables[table_name].fields(only_names=False).items():
                if type(field) == ForeignKeyField:
                    self.__fk[table_name][field_name] = field.rel_model._meta.name

        # Show resulting architecture
        if show_architecture:
            self.print_architecture()

        return self

    def get_path(self) -> Tuple[str, str]:
        """
        Access the Database file path.
        """

        return self.__database_dir, self.__database_name

    def print_architecture(self):
        """
        Print the content of the Database with Table(s) and their Field(s).
        """

        print(f'\nDATABASE {self.__database_name}.db')
        print(''.join([table.description(indent=True, name=name) for name, table in self.__tables.items()]))

    def get_architecture(self):
        """
        Get the content of the Database with Table(s) and their Field(s).
        """

        architecture = {}
        for table_name in self.__tables.keys():
            description = self.__tables[table_name].description()
            fields = description.split('  - ')
            architecture[table_name] = [field[:-1] for field in fields[1:]]
        return architecture

    def get_tables(self,
                   only_names: bool = True):
        """
        Get the names of created Tables in the Database.

        :param only_names: If True, only the names of the Tables will be returned in a List, otherwise the Tables
                           themselves are returned in a Dict.
        """

        if only_names:
            return list(self.__tables.keys())
        return self.__tables

    def get_fields(self,
                   table_name: str,
                   only_names: bool = True):
        """
        Get the names of the Field(s) of a Tables of the Database.

        :param table_name: Name of the Table.
        :param only_names: If False, returns a dict containing {'table_name': Table}.
        """

        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown table with name {table_name}")
        return self.__tables[table_name].fields(only_names=only_names)

    def create_table(self,
                     table_name: str,
                     storing_table: bool = True,
                     fields: Optional[Union[FieldType, List[FieldType]]] = None):
        """
        Add a new Table to the Database with customizable Fields.

        :param table_name: Name of the Table to add to the Database.
        :param storing_table: Specify whether the Table must be a storing or an exchange Table.
        :param fields: Name(s), type(s) and default value(s) of the Field(s) to add to the Table.
        """

        table_name = self.make_name(table_name)
        self.__create(table_name=table_name,
                      existing_table=False,
                      storing_table=storing_table,
                      fields=fields)

    def create_fields(self,
                      table_name: str,
                      fields: Union[FieldType, List[FieldType]]):
        """
        Add new Fields to a Table.

        :param table_name: Name of the Table on which to add the new Fields.
        :param fields: Name(s), type(s) and default value(s) of the Field(s) to add to the Table.
        """

        table_name = self.make_name(table_name)
        self.__create(table_name=table_name,
                      existing_table=True,
                      fields=fields)

    def __create(self,
                 table_name: str,
                 existing_table: bool,
                 storing_table: bool = True,
                 fields: Optional[Union[FieldType, List[FieldType]]] = None):

        # Create the table
        if not existing_table:
            self.__new_table(table_name=table_name,
                             storing_table=storing_table)

        # Extend the fields
        fields = [fields] if type(fields) != list and fields is not None else fields
        self.__new_fields(table_name=table_name,
                          fields=fields)

    def __new_table(self,
                    table_name: str,
                    storing_table: bool):

        if table_name not in self.__tables:

            # Create the new Table
            table_class = StoringTable if storing_table else ExchangeTable
            self.__tables[table_name] = type(table_name, (table_class,), dict(table_class.__dict__))
            self.__tables[table_name]._meta.name = table_name
            self.__fk[table_name] = {}

            # Connect the Table the Database
            self.__tables[table_name].connect(self.__database)

            # Add a DateTimeField to exchange tables
            if not storing_table:
                self.__new_fields(table_name=table_name,
                                  fields=[('_dt_', datetime)])

    def __new_fields(self,
                     table_name: str,
                     fields: List[FieldType]):

        if fields is not None:
            table = self.__tables[table_name]

            # Add each Field to the Table
            for field in fields:

                # Define name, type and default value
                field_name, field_type = field[0], field[1]
                field_default = '_null_' if len(field) == 2 else field[2]

                # As peewee.Model creates a new attribute named field_name, check that this attribute does not exist
                if field_name in [m[0] for m in getmembers(table)]:
                    raise ValueError(f"Tried to create a field '{field_name}' in the Table '{table_name}'. "
                                     f"You are not allowed to create a field with this name, please rename it.")

                # Extend the Table
                if field_name not in table.fields():
                    # FK
                    if type(field_type) == str:
                        if (fk_table_name := self.make_name(field_type)) not in self.__tables.keys():
                            raise ValueError(f"Cannot create the ForeignKey '{fk_table_name}' since this Table does not"
                                             f"exists. Created Tables so far: {self.__tables.keys()}")
                        table.extend_fk(self.__tables[fk_table_name], field_name)
                        self.__fk[table_name][field_name] = fk_table_name
                    else:
                        table.extend(field_name, field_type, field_default)

    def register_pre_save_signal(self,
                                 table_name: str,
                                 handler: Callable,
                                 name: Optional[str] = None):
        """
        Connect a pre_save signal from a Table to a handler.

        :param table_name: Name of the Table that will be sender.
        :param handler: Executable code.
        :param name: Name of the signal.
        """

        table_name = self.make_name(table_name)
        self.__signals.append(('pre_save', pre_save, table_name, self.__on_save_signal(handler), name))

    def register_post_save_signal(self,
                                  table_name: str,
                                  handler: Callable,
                                  name: Optional[str] = None):
        """
        Connect a post_save signal from a Table to a handler.

        :param table_name: Name of the Table that will be sender.
        :param handler: Executable code.
        :param name: Name of the signal.
        """

        table_name = self.make_name(table_name)
        self.__signals.append(('post_save', post_save, table_name, self.__on_save_signal(handler), name))

    @staticmethod
    def __on_save_signal(handler: Callable):

        def signal_handler(sender, instance, **kwargs):
            # Convert received information into Table name and data
            table_name = sender.get_name()
            handler(table_name, instance.__data__)

        return signal_handler

    def connect_signals(self):
        """
        Connect the registered signals between Tables and handlers.
        """

        for signal in self.__signals:

            # Get the information of registered signals
            signal_type, signal_class, table_name, handler, name = signal

            # Check if the Table has been created
            if table_name not in self.__tables:
                print(f"WARNING: Signal '{signal_type}' was not connected with Table '{table_name}' as sender since "
                      f"it was not created.")
            else:
                signal_class.connect(receiver=handler,
                                     sender=self.__tables[table_name],
                                     name=name)
        self.__signals = []

    def add_data(self,
                 table_name: str,
                 data: Dict[str, Any]):
        """
        Execute a line insert query. Return the index of the new line in the Table.

        :param table_name: Name of the Table.
        :param data: New line of the Table.
        """

        table_name = self.make_name(table_name)
        return self.__add_data(table_name=table_name,
                               data=data)

    def add_batch(self,
                  table_name: str,
                  batch: Dict[str, List[Any]]):
        """
        Execute a batch insert query. Return the indices of the new lines in the Table.

        :param table_name: Name of the Table.
        :param batch: New lines of the Table.
        """

        table_name = self.make_name(table_name)
        # Check that the batch is well-formed
        if table_name in self.__fk:
            batch_values = [batch[key] for key in set(batch.keys()) - set(self.__fk[table_name])]
            if len(unique(samples := [len(b) for b in batch_values])) != 1:
                raise ValueError(f"The number of samples per batch must be the same for all fields. Number of samples "
                                 f"received per field: {dict(zip(batch.keys(), samples))}")
        return self.__add_data(table_name=table_name,
                               data=batch,
                               batched=True)

    def __add_data(self,
                   table_name: str,
                   data: Union[Dict[str, Any], Dict[str, List[Any]]],
                   batched: Optional[bool] = False):

        # Unpack kwargs
        fields_names = list(data.keys())
        fields_values = list(data.values())
        fields_types = []
        for name, value in zip(fields_names, fields_values):
            if table_name in self.__fk and name in self.__fk[table_name]:
                fields_types.append(self.__fk[table_name][name])
            elif batched:
                fields_types.append(type(value[0]))
            else:
                fields_types.append(type(value))

        # Check table existence
        if table_name not in self.__tables:
            self.create_table(table_name=table_name, fields=list(zip(fields_names, fields_types)))
        table = self.__tables[table_name]

        # Check fields existence
        undefined_fields = set(fields_names) - set(table.fields())
        if len(undefined_fields) > 0:
            # Empty table: add fields on the fly
            if len(table.select()) == 0:
                self.create_fields(table_name=table_name,
                                   fields=list(zip(fields_names, fields_types)))
            # Non-empty table
            else:
                raise ValueError(f"[{self.__class__.__name__}]  Some fields where not defined in table {table}."
                                 f" As table {table} is non-empty, please define first the following fields :"
                                 f" {list(undefined_fields)}.")

        # Check FK data
        fk_fields = set(fields_names).intersection(set(self.__fk[table_name].keys()))
        for fk_field in fk_fields:
            idx = fields_names.index(fk_field)
            if type(fields_values[idx]) == dict:
                fk_table_name = self.__fk[table_name][fk_field]
                line = self.__add_data(table_name=fk_table_name,
                                       data=fields_values[idx],
                                       batched=batched)
                fields_values[idx] = line

        # Add the data to Table
        return table.add_data(fields_names=fields_names,
                              fields_values=fields_values,
                              batched=batched)

    def update(self,
               table_name: str,
               data: Dict[str, Any],
               line_id: int = -1):
        """
        Update a line of a Table.

        :param table_name: Name of the Table on which to perform the query.
        :param data: Updated data of the line.
        :param line_id: Index of the line to update.
        """

        # Check table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown table with name {table_name}")
        table = self.__tables[table_name]

        # Unpack data
        fields_names = list(data.keys())
        fields_values = list(data.values())

        # Define the line index
        nb_line = self.nb_lines(table_name=table_name)
        if line_id < 0:
            line_id += nb_line + 1
        elif line_id > nb_line:
            line_id = nb_line

        # Check fields existence
        undefined_fields = set(fields_names) - set(table.fields())
        if len(undefined_fields) > 0:
            raise ValueError(f"[{self.__class__.__name__}]  Some fields where not defined in table {table}."
                             f" As table {table} is non-empty, please define first the following fields :"
                             f" {list(undefined_fields)}.")

        # Check FK data
        fk_fields = set(fields_names).intersection(set(self.__fk[table_name].keys()))
        for fk_field in fk_fields:
            idx = fields_names.index(fk_field)
            if type(fields_values[idx]) == dict:
                fk_table_name = self.__fk[table_name][fk_field]
                fk_id = self.get_line(table_name=table_name,
                                      fields=fk_field,
                                      line_id=line_id)[fk_field]
                self.update(table_name=fk_table_name,
                            data=fields_values[idx],
                            line_id=fk_id)
            del fields_names[idx]
            del fields_values[idx]

        # Update query
        table.update(dict(zip(fields_names, fields_values))).where(table.id == line_id).execute()

    def get_line(self,
                 table_name: str,
                 fields: Optional[Union[str, List[str]]] = None,
                 line_id: int = -1,
                 joins: Optional[Union[str, List[str]]] = None):
        """
        Get a line of a Table.

        :param table_name: Name of the Table on which to perform the query.
        :param fields: Name(s) of the Field(s) to request.
        :param line_id: Index of the line to get.
        :param joins: Name(s) of Table(s) to join to the selection.
        """

        # Check the Table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown table with name {table_name}")
        table = self.__tables[table_name]

        # Define the fields to select
        fields_selection = ()
        if fields is not None:
            fields_selection += (table.id,)
            fields = [fields] if type(fields) == str else fields
            for field in fields:
                if field in table.fields():
                    fields_selection += (table.fields(only_names=False)[field],)
            if joins is not None:
                joins = [joins] if type(joins) == str else joins
                for j in joins:
                    if j in self.__fk[table_name].values() and j not in fields:
                        field_name = list(self.__fk[table_name].keys())[
                            list(self.__fk[table_name].values()).index(j)]
                        fields_selection += (table.fields(only_names=False)[field_name],)

        # Define the index of the line to select
        nb_line = self.nb_lines(table_name=table_name)
        if line_id < 0:
            line_id += nb_line + 1
        elif line_id > nb_line:
            line_id = nb_line

        # Selection query
        data = table.select(*fields_selection).where(table.id == line_id).dicts()[0]

        # Join
        if joins is not None:
            joins = [joins] if type(joins) == str else joins
            for j in joins:
                if j in self.__fk[table_name].values():
                    field_name = list(self.__fk[table_name].keys())[list(self.__fk[table_name].values()).index(j)]
                    if field_name in data:
                        data[field_name] = self.get_line(table_name=j,
                                                         fields=fields,
                                                         line_id=data[field_name],
                                                         joins=j)

        return data

    def get_lines(self,
                  table_name: str,
                  fields: Optional[Union[str, List[str]]] = None,
                  lines_id: Optional[List[int]] = None,
                  lines_range: Optional[List[int]] = None,
                  joins: Optional[Union[str, List[str]]] = None,
                  batched: bool = False):
        """
        Get a set of lines of a Table.

        :param table_name: Name of the Table on which to perform the query.
        :param fields: Name(s) of the Field(s) to select.
        :param lines_id: Indices of the lines to get. If not specified, 'lines_range' value will be used.
        :param lines_range: Range of indices of the lines to get. If not specified, all lines will be selected.
        :param joins: Name(s) of Table(s) to join to the selection.
        :param batched: If True, data is returned as one batch per field. Otherwise, data is returned as list of lines.
        """

        # Check table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown table with name {table_name}")
        table = self.__tables[table_name]

        # Define the fields to select
        fields_selection = ()
        if fields is not None:
            fields_selection += (table.id,)
            fields = [fields] if type(fields) == str else fields
            for field in fields:
                if field in table.fields():
                    fields_selection += (table.fields(only_names=False)[field],)
            if joins is not None:
                joins = [joins] if type(joins) == str else joins
                for j in joins:
                    if j in self.__fk[table_name].values() and j not in fields:
                        field_name = list(self.__fk[table_name].keys())[
                            list(self.__fk[table_name].values()).index(j)]
                        fields_selection += (table.fields(only_names=False)[field_name],)

        # Define the indices of lines to select
        if lines_id is None:
            if lines_range is not None and len(lines_range) != 2:
                raise ValueError("The range of lines must contains the first and the last line indices.")
            nb_line = self.nb_lines(table_name=table_name)
            first_line_id = lines_range[0] if lines_range is not None else 1
            last_line_id = lines_range[1] if lines_range is not None else nb_line
            _slice = [first_line_id, last_line_id]
            for i, idx in enumerate(_slice):
                if idx < 0:
                    _slice[i] += nb_line + 1
                elif idx > nb_line:
                    _slice[i] = nb_line
            _slice[1] = _slice[0] + 1 if _slice[1] < _slice[0] else _slice[1] + 1
            lines_id = range(*_slice)

        # Selection query
        query = table.select(*fields_selection).where(table.id << lines_id).dicts()

        # Return the lines as batch or as list of lines
        lines: Union[Dict[str, List[Any]], List[Dict[str, Any]]]
        if batched:
            lines = dict(zip(query[0].keys(),
                             [[query[i][key] for i in range(len(query))] for key in query[0].keys()]))
        else:
            lines = [line for line in query]

        # Join
        if joins is not None:
            joins = [joins] if type(joins) == str else joins
            for j in joins:
                if j in self.__fk[table_name].values():
                    field_name = list(self.__fk[table_name].keys())[
                        list(self.__fk[table_name].values()).index(j)]
                    dict_keys = lines.keys() if batched else lines[0].keys()
                    if field_name in dict_keys:
                        lines_id = lines[field_name] if batched else [line[field_name] for line in lines]
                        data = self.get_lines(table_name=j,
                                              fields=fields,
                                              lines_id=lines_id,
                                              joins=joins,
                                              batched=batched)

                        if batched:
                            lines[field_name] = data
                        else:
                            for i, l in enumerate(data):
                                lines[i][field_name] = l

        return lines

    def nb_lines(self,
                 table_name: str):
        """
        Return the number of entries on a Table.

        :param table_name: Name of the Table.
        """

        # Check the Table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown table with name {table_name}")

        # Get the number of entries
        return self.__tables[table_name].select().count()

    @property
    def memory_size(self):
        """
        Return the Database file memory size in bytes.
        """

        return getsize(join(self.__database_dir, f'{self.__database_name}.db'))

    def close(self, erase_file: bool = False):
        """
        Close the Database.

        :param erase_file: If True, the Database file will be erased.
        """

        self.__database.close()
        if erase_file and exists(database_path := join(self.__database_dir, f'{self.__database_name}.db')):
            remove(database_path)

    def rename_table(self,
                     table_name: str,
                     new_table_name: str):
        """
        Rename a Table of the Database.

        :param table_name: Current name of the Table to rename.
        :param new_table_name: New name of the Table.
        """

        # Check the Table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown table with name {table_name}")

        # Renaming
        self.__tables[new_table_name] = self.__tables.pop(table_name)
        self.__tables[new_table_name].rename_table(table_name, new_table_name)

    def rename_field(self,
                     table_name: str,
                     field_name: str,
                     new_field_name: str):
        """
        Rename a Field of a Table of the Database.

        :param table_name: Name of the Table.
        :param field_name: Current name of the Field to rename.
        :param new_field_name: New name of the Field.
        """

        # Check the Table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown Table with name '{table_name}'")

        # Check the field existence
        if field_name not in self.__tables[table_name].fields():
            raise ValueError(f"Unknown Field with name '{field_name}' for Table '{table_name}'")

        # Renaming
        self.__tables[table_name].rename_field(field_name, new_field_name)

    def remove_table(self,
                     table_name: str):
        """
        Remove a Table from the Database.

        :param table_name: Name of the Table.
        """

        # Check the table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown Table with name '{table_name}'")

        # Remove the Table
        self.__database.drop_tables(self.__tables[table_name])
        del self.__tables[table_name]

    def remove_field(self,
                     table_name: str,
                     field_name: str):
        """
        Remove a Field of a Table of the Database.

        :param table_name: Name of the Table.
        :param field_name: Current name of the Field to remove.
        """

        # Check the Table existence
        table_name = self.make_name(table_name)
        if table_name not in self.__tables:
            raise ValueError(f"Unknown Table with name '{table_name}'")

        # Check the field existence
        if field_name not in self.__tables[table_name].fields():
            raise ValueError(f"Unknown Field with name '{field_name}' for Table '{table_name}'")

        # Renaming
        self.__tables[table_name].remove_field(field_name)

    def export(self,
               exporter: str,
               filename: str,
               tables: Optional[Union[str, List[str]]] = None) -> None:
        """
        Export the Database to a CSV or JSON file.

        :param exporter: Exporter type ('json' or 'csv').
        :param filename: Exported filename.
        :param tables: Tables to export.
        """

        # Check exporter format
        exporter = exporter.lower()
        if exporter not in ['json', 'csv']:
            raise ValueError(f"Unknown exporter with name {exporter}. Available exporters are ['json', 'csv'].")

        # Set good file extension
        file_path = filename.split(sep)
        file_name = file_path.pop(-1)
        file_name = file_name if len(file_name.split('.')) == 1 else file_name.split('.')[0]
        filename = join(*file_path[:-1], file_name)

        # Get the tables to export
        tables = self.get_tables() if tables is None else tables
        tables = [tables] if type(tables) != list else tables
        for table in tables:
            if table not in self.get_tables():
                raise ValueError(f"The following Table does not exist: {table}")

        # Export each table
        # Todo: see 'at once' version
        for table in tables:
            _filename = filename + f'_{table}.{exporter}'
            if exporter == 'json':
                query = self.get_lines(table_name=table, batched=True)
                Exporter.export_json(filename=_filename, query=query)
            else:
                query = self.__tables[table].select().tuples()
                Exporter.export_csv(filename=_filename, query=query)
