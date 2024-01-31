from os.path import exists, join
from os import system

from SSD.Core.Storage import Database

# Assert DB existence
if not exists(join('my_databases', 'database_1.db')) or not exists(join('my_databases', 'database_2.db')):
    system('python3 write_db.py')


# Load an existing Database storage file
db_1 = Database(database_dir='my_databases',
                database_name='database_1')
db_1.load(show_architecture=True)

# Condensed code
db_2 = Database(database_dir='my_databases',
                database_name='database_2').load(show_architecture=True)


# Read a few lines
print("\nREAD in database_1.db")
for i in range(1, 6):
    print(db_1.get_line(table_name='Rawdata',
                        fields='array',
                        line_id=i))
    print(db_1.get_line(table_name='Stats',
                        fields=['mean', 'positive_values'],
                        line_id=i))

# Read a batch of lines
print("\nREAD in database_2.db")
print(db_2.get_lines(table_name='Rawdata',
                     fields='array',
                     lines_range=[1, -1],
                     batched=True))
print(db_2.get_lines(table_name='Stats',
                     fields=['mean', 'positive_values'],
                     lines_range=[1, -1],
                     batched=True))


# Close Databases
db_1.close()
db_2.close()
