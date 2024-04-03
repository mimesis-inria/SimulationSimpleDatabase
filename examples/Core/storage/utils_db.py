import os
from numpy.random import uniform

from SSD.Core.Storage import Database, merge, rename_tables, rename_fields, remove_table, remove_field, export


# Create new Databases
for i in [1, 2]:
    db = Database(database_dir='my_databases',
                  database_name=f'database_{i}').new(remove_existing=True)
    db.create_table(table_name=f'Table_{i}',
                    storing_table=True,
                    fields=[('value', float), ('is_positive', bool)])
    new_values = [round(uniform(low=-1, high=1), 2) for _ in range(5)]
    db.add_batch(table_name=f'Table_{i}',
                 batch={'value': new_values,
                        'is_positive': [x > 0 for x in new_values]})
    db.close()
os.chdir('my_databases')

# Merge Databases
merge(database_files=['database_1', 'database_2'],
      new_database_file='database_3',
      remove_existing=True)

# Renaming Tables and Fields
rename_tables(database_file='database_3',
              renamed_tables=('Table_1', 'Table'))
rename_fields(database_file='database_3',
              table_name='Table',
              renamed_fields=[('value', 'data'), ('is_positive', 'flag')])

# Remove Tables and Fields
remove_field(database_file='database_3',
             table_name='Table_2',
             fields='is_positive')
remove_table(database_file='database_3',
             table_names='Table_2')

# Export to JSON and CSV
export(database_file='database_3',
       exporter='json')
export(database_file='database_3',
       exporter='csv')
