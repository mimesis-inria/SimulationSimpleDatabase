from peewee import IntegerField, ForeignKeyField, BareField, CompositeKey, AutoField, DeferredForeignKey, SQL
from playhouse.reflection import Introspector, SqliteDatabase, SqliteMetadata, UnknownField
import warnings

from SSD.Core.Storage.adaptive_table import StoringTable, ExchangeTable
from SSD.Core.Storage.numpy_field import NumpyField


def generate_models(database, schema=None, **options):

    # EXTENSION: Use extended inspector
    introspector = ExtendedIntrospector.from_database(database, schema=schema)
    return introspector.generate_models(**options)


class ExtendedSqliteMetadata(SqliteMetadata):

    def __init__(self, database):
        super().__init__(database)
        # EXTENSION: Extend the columns mapper with the new NumpyField
        self.column_map['numpy'] = NumpyField


class ExtendedIntrospector(Introspector):

    @classmethod
    def from_database(cls, database, schema=None):
        if isinstance(database, SqliteDatabase):
            # EXTENSION: Use extended metadata class
            metadata = ExtendedSqliteMetadata(database)
            return cls(metadata, schema=schema)
        return Introspector.from_database(database, schema)

    def generate_models(self, skip_invalid=False, table_names=None, literal_column_names=False, bare_fields=False,
                        include_views=False):

        database = self.introspect(table_names, literal_column_names, include_views)
        models = {}
        pending = set()

        def _create_model(table, models):
            pending.add(table)
            for foreign_key in database.foreign_keys[table]:
                dest = foreign_key.dest_table

                if dest not in models and dest != table:
                    if dest in pending:
                        warnings.warn('Possible reference cycle found between '
                                      '%s and %s' % (table, dest))
                    else:
                        _create_model(dest, models)

            primary_keys = []
            columns = database.columns[table]
            for column_name, column in columns.items():
                if column.primary_key:
                    primary_keys.append(column.name)

            multi_column_indexes = database.multi_column_indexes(table)
            column_indexes = database.column_indexes(table)

            class Meta:
                indexes = multi_column_indexes
                table_name = table

            # Fix models with multi-column primary keys.
            composite_key = False
            if len(primary_keys) == 0:
                if 'id' not in columns:
                    Meta.primary_key = False
                else:
                    primary_keys = columns.keys()

            if len(primary_keys) > 1:
                Meta.primary_key = CompositeKey(*[
                    field.name for col, field in columns.items()
                    if col in primary_keys])
                composite_key = True

            attrs = {'Meta': Meta}
            for column_name, column in columns.items():
                FieldClass = column.field_class
                if FieldClass is not ForeignKeyField and bare_fields:
                    FieldClass = BareField
                elif FieldClass is UnknownField:
                    FieldClass = BareField

                params = {
                    'column_name': column_name,
                    'null': column.nullable}
                if column.primary_key and composite_key:
                    if FieldClass is AutoField:
                        FieldClass = IntegerField
                    params['primary_key'] = False
                elif column.primary_key and FieldClass is not AutoField:
                    params['primary_key'] = True
                if column.is_foreign_key():
                    if column.is_self_referential_fk():
                        params['model'] = 'self'
                    else:
                        dest_table = column.foreign_key.dest_table
                        if dest_table in models:
                            params['model'] = models[dest_table]
                        else:
                            FieldClass = DeferredForeignKey
                            params['rel_model_name'] = dest_table
                    if column.to_field:
                        params['field'] = column.to_field

                    # Generate a unique related name.
                    params['backref'] = '%s_%s_rel' % (table, column_name)

                if column.default is not None:
                    constraint = SQL('DEFAULT %s' % column.default)
                    params['constraints'] = [constraint]

                if not column.is_primary_key():
                    if column_name in column_indexes:
                        if column_indexes[column_name]:
                            params['unique'] = True
                        elif not column.is_foreign_key():
                            params['index'] = True
                    else:
                        params['index'] = False

                attrs[column.name] = FieldClass(**params)

            # EXTENSION: BaseModel must inherit from our adaptive models
            class BaseModel(ExchangeTable if '_dt_' in database.columns[table] else StoringTable):
                class Meta:
                    database = self.metadata.database
                    schema = self.schema

            try:
                models[table] = type(str(table), (BaseModel,), attrs)
            except ValueError:
                if not skip_invalid:
                    raise
            finally:
                if table in pending:
                    pending.remove(table)

        # Actually generate Model classes.
        for table, model in sorted(database.model_names.items()):
            if table not in models:
                _create_model(table, models)

        return models, database
