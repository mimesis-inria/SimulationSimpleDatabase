from numpy import ndarray, where
from numpy.random import uniform

from SSD.Core.Storage import Database

# Create a new Database object and a new storage file
db = Database(database_dir='my_databases',
              database_name='database_fk').new(remove_existing=True)

# Create new Tables with new Fields (including ForeignKeyField)
db.create_table(table_name='Stats',
                storing_table=True,
                fields=[('mean', float, 0.), ('positive_values', int, 0)])
db.create_table(table_name='RawData',
                storing_table=True,
                fields=[('array', ndarray), ('stats', 'Stats')])

# Show the architecture
db.print_architecture()

# Add a line of data Table per Table
new_array = uniform(low=-1, high=1, size=(10,))
stats = db.add_data(table_name='Stats',
                    data={'mean': new_array.mean(),
                          'positive_values': len(where(new_array > 0)[0])})
db.add_data(table_name='RawData',
            data={'array': new_array,
                  'stats': stats})

# Add a line of data only using the referencing Table
new_array = uniform(low=-1, high=1, size=(10,))
db.add_data(table_name='RawData',
            data={'array': new_array,
                  'stats': {'mean': new_array.mean(),
                            'positive_values': len(where(new_array > 0)[0])}})

# Add a batch of data Table per Table
new_arrays = [uniform(low=-1, high=1, size=(10,)) for _ in range(5)]
new_stats = [db.add_data(table_name='Stats',
                         data={'mean': new_array.mean(),
                               'positive_values': len(where(new_array > 0)[0])}) for new_array in new_arrays]
db.add_batch(table_name='RawData',
             batch={'array': new_arrays,
                    'stats': new_stats})

# Add a batch of data only using the referencing Table
new_arrays = [uniform(low=-1, high=1, size=(10,)) for _ in range(5)]
db.add_batch(table_name='RawData',
             batch={'array': new_arrays,
                    'stats': {'mean': [new_array.mean() for new_array in new_arrays],
                              'positive_values': [len(where(new_array > 0)[0]) for new_array in new_arrays]}})

# Load the Database
db.close()
db = Database(database_dir='my_databases',
              database_name='database_fk').load(show_architecture=True)

# Read a line of data
print("\nREAD row=1")
raw_data = db.get_line(table_name='RawData', line_id=1, fields=['array', 'stats'])
stats = db.get_line(table_name='Stats', line_id=raw_data['stats'], fields='mean')
print(f"rawdata={raw_data}")
print(f"stats={stats}")

# Read a line of data only using the referencing Table
print("\nREAD row=2")
raw_data = db.get_line(table_name='RawData', line_id=2, joins='Stats', fields=['array', 'mean'])
print(f"rawdata={raw_data}")

# Read a batch of lines
print("\nREAD row=3-5")
raw_data = db.get_lines(table_name='RawData',
                        lines_range=[3, 5],
                        batched=True)
stats = db.get_lines(table_name='Stats',
                     lines_id=raw_data['stats'],
                     batched=True)
print(f"rawdata={raw_data}")
print(f"stats={stats}")

# Read a batch of lines only using the referencing Table
print("\nREAD row=6-8")
raw_data = db.get_lines(table_name='RawData',
                        lines_range=[6, 8],
                        joins='Stats',
                        batched=True)
print(f"rawdata={raw_data}")

# Updating a line of data Table per Table
print("\nUPDATE row=1 (before):")
print(db.get_line(table_name='RawData',
                  line_id=1,
                  joins='Stats'))
new_array = uniform(low=-1, high=1, size=(10,))
raw_data = db.get_line(table_name='RawData',
                       fields='stats',
                       line_id=1)
db.update(table_name='Stats',
          line_id=raw_data['stats'],
          data={'mean': new_array.mean(),
                'positive_values': len(where(new_array > 0)[0])})
db.update(table_name='RawData',
          line_id=1,
          data={'array': new_array})
print("UPDATE row=1 (after):")
print(db.get_line(table_name='RawData',
                  line_id=1,
                  joins='Stats'))

# Updating a line of data only using the referencing Table
print("\nUPDATE row=2 (before):")
print(db.get_line(table_name='RawData',
                  line_id=2,
                  joins='Stats'))
new_array = uniform(low=-1, high=1, size=(10,))
db.update(table_name='RawData',
          line_id=2,
          data={'array': new_array,
                'stats': {'mean': new_array.mean(),
                          'positive_values': len(where(new_array > 0)[0])}})
print("UPDATE row=2 (after):")
print(db.get_line(table_name='RawData',
                  line_id=2,
                  joins='Stats'))
