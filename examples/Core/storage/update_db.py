from os.path import exists, join
from os import system
from numpy import where
from numpy.random import uniform

from SSD.Core.Storage import Database


# Assert DB existence
if not exists(join('my_databases', 'database_1.db')) or not exists(join('my_databases', 'database_2.db')):
    system('python3 write_db.py')


# Load an existing Database storage file
db = Database(database_dir='my_databases',
              database_name='database_1').load(show_architecture=True)


# Updating data
new_array = uniform(low=-1, high=1, size=(10,))
new_mean = new_array.mean()
new_positive = len(where(new_array > 0)[0])
print("\nBEFORE UPDATE:")
print(db.get_line(table_name='RawData', line_id=1))
print(db.get_line(table_name='Stats', line_id=1))
db.update(table_name='RawData',
          line_id=1,
          data={'array': new_array})
db.update(table_name='Stats',
          line_id=1,
          data={'mean': new_mean, 'positive_values': new_positive})
print("\nAFTER UPDATE:")
print(db.get_line(table_name='RawData', line_id=1))
print(db.get_line(table_name='Stats', line_id=1))


# Close Database
db.close()
