from typing import Dict, Type, Any, Union, List, Optional
from peewee import IntegerField, FloatField, TextField, BooleanField, BlobField, DateTimeField, ForeignKeyField, Field
from peewee import chunked
from playhouse.signals import Model, pre_save, post_save
from playhouse.migrate import migrate, SqliteMigrator, SqliteDatabase
from numpy import ndarray
from datetime import datetime

from SSD.Core.Storage.numpy_field import NumpyField


class AdaptiveTable(Model):
    role: str = 'Adaptive'
    table_type: Dict[Type, Field] = {int: IntegerField,
                                     float: FloatField,
                                     str: TextField,
                                     bool: BooleanField,
                                     datetime: DateTimeField,
                                     ndarray: NumpyField}

    class Meta:
        database = None
        only_dirty_fields = True

    @classmethod
    def get_name(cls) -> str:

        return cls._meta.table_name

    @classmethod
    def database(cls) -> SqliteDatabase:

        return cls._meta.database

    @classmethod
    def fields(cls, only_names: bool = True) -> Union[List[str], Dict[str, Field]]:

        return list(cls._meta.fields.keys()) if only_names else cls._meta.fields

    @classmethod
    def connect(cls, database: SqliteDatabase) -> None:

        cls.bind(database)
        cls.database().create_tables([cls])

    @classmethod
    def extend(cls,
               field_name: str,
               data_type: Type,
               default_value: Any) -> None:

        migrator = SqliteMigrator(cls.database())
        atts = {'null': True}
        if default_value != '_null_':
            if type(default_value) != data_type:
                raise TypeError(
                    f"The default value type for field {field_name} of table {cls._meta.name} must be {data_type},"
                    f" not {type(default_value)}.")
            atts['default'] = default_value
        elif data_type == datetime:
            atts['default'] = datetime.now
        field = cls.table_type.get(data_type, BlobField)(**atts)
        migrate(migrator.add_column(cls._meta.name, field_name, field))
        cls._meta.add_field(field_name, field)

    @classmethod
    def extend_fk(cls,
                  model: Model,
                  field_name: str) -> None:

        migrator = SqliteMigrator(cls.database())
        field = ForeignKeyField(model=model, backref=field_name, null=True, field=model._meta.primary_key)
        migrate(migrator.add_column(cls._meta.name, field_name, field))
        cls._meta.add_field(field_name, field)

    @classmethod
    def rename_table(cls,
                     old_table_name: str,
                     new_table_name: str) -> None:

        migrator = SqliteMigrator(cls.database())
        migrate(migrator.rename_table(old_table_name, new_table_name))

    @classmethod
    def rename_field(cls,
                     old_field_name: str,
                     new_field_name: str) -> None:

        migrator = SqliteMigrator(cls.database())
        migrate(migrator.rename_column(cls._meta.name, old_field_name, new_field_name))
        cls._meta.add_field(new_field_name, getattr(cls, old_field_name))
        cls._meta.remove_field(old_field_name)

    @classmethod
    def remove_field(cls,
                     field_name: str) -> None:

        migrator = SqliteMigrator(cls.database())
        migrate(migrator.drop_column(cls._meta.name, field_name))
        cls._meta.remove_field(field_name)

    @classmethod
    def description(cls,
                    indent: bool = False,
                    name: Optional[str] = None) -> str:

        indent = '  ' if indent else ''
        name = cls.get_name() if name is None else name
        desc = f'{indent}* {cls.role}Table "{name}"\n'
        for field in cls._meta.sorted_fields:
            if type(field) == ForeignKeyField:
                field_type = f'(FK -> {field.rel_model._meta.name})'
            else:
                field_type = f'({field.field_type})'

            desc += f'{indent}  - {field.name} {field_type}'
            desc += f' (default)\n' if field.name in ['id', '_dt_'] else '\n'
        return desc

    @classmethod
    def add_data(cls,
                 fields_names: List[str],
                 fields_values: List[Any],
                 batched: bool = False) -> Union[int, List[int]]:

        pass


class StoringTable(AdaptiveTable):
    role: str = 'Storing'

    @classmethod
    def add_data(cls,
                 fields_names: List[str],
                 fields_values: List[Any],
                 batched: bool = False) -> Union[int, List[int]]:

        if not batched:
            line = cls(**dict(zip(fields_names, fields_values)))
            line.save()
            return line.id

        else:
            fields = [getattr(cls, field) for field in fields_names]
            batch = [tuple(samples) for samples in zip(*fields_values)]
            n = cls.select().count()
            with cls.database().atomic():
                for chunk in chunked(batch, 100):
                    cls.insert_many(chunk, fields=fields).execute()
            N = cls.select().count()
            return [cls.get_by_id(i + 1).id for i in range(n, N)]


class ExchangeTable(AdaptiveTable):
    role: str = 'Exchange'

    @classmethod
    def add_data(cls,
                 fields_names: List[str],
                 fields_values: List[Any],
                 batched: bool = False) -> Union[int, List[int]]:

        if not batched:
            cls.delete().execute()
            line = cls(**dict(zip(fields_names, fields_values)))
            line.save()
            return line.id

        else:
            fields = [getattr(cls, field) for field in fields_names]
            batch = [tuple(samples) for samples in zip(*fields_values)]
            cls.delete().execute()
            pre_save.send(cls, created=False)
            n = cls.select().count()
            with cls.database().atomic():
                for chunk in chunked(batch, 100):
                    cls.insert_many(chunk, fields=fields).execute()
            N = cls.select().count()
            post_save.send(cls, created=False)
            return [cls.get_by_id(i + 1).id for i in range(n, N)]
