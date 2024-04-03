from numpy import ndarray, where
from numpy.random import uniform

from SSD.Core.Storage import Database


# Create a new Database object and a new storage file
db_1 = Database(database_dir='my_databases',
                database_name='database_1')
db_1.new(remove_existing=True)

# Condensed code
db_2 = Database(database_dir='my_databases',
                database_name='database_2').new(remove_existing=True)


# Create new Tables with new Fields
db_1.create_table(table_name='RawData',
                  storing_table=True)
db_1.create_fields(table_name='RawData',
                   fields=('array', ndarray))
db_1.create_table(table_name='Stats',
                  storing_table=True)
db_1.create_fields(table_name='Stats',
                   fields=[('mean', float, 0.), ('positive_values', int, 0)])

# Condensed code
db_2.create_table(table_name='RawData',
                  storing_table=True,
                  fields=('array', ndarray))
db_2.create_table(table_name='Stats',
                  storing_table=True,
                  fields=[('mean', float, 0.), ('positive_values', int, 0)])


# Show the architectures
db_1.print_architecture()
db_2.print_architecture()


# Add a few lines
for _ in range(5):
    new_array = uniform(low=-1, high=1, size=(10,))
    new_mean = new_array.mean()
    new_positive = len(where(new_array > 0)[0])
    db_1.add_data(table_name='RawData',
                  data={'array': new_array})
    db_1.add_data(table_name='Stats',
                  data={'mean': new_mean, 'positive_values': new_positive})

# Condensed code
new_arrays = [uniform(low=-1, high=1, size=(10,)) for _ in range(5)]
new_means = [new_array.mean() for new_array in new_arrays]
new_positives = [len(where(new_array > 0)[0]) for new_array in new_arrays]
db_2.add_batch(table_name='RawData',
               batch={'array': new_arrays})
db_2.add_batch(table_name='Stats',
               batch={'mean': new_means, 'positive_values': new_positives})


# Close Databases
db_1.close()
db_2.close()
