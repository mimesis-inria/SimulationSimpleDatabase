from numpy import ndarray
from numpy.random import uniform

from SSD.Core.Storage import Database

# Create a new Database object and a new storage file
db = Database(database_dir='my_databases',
              database_name='database_3').new(remove_existing=True)

# Create new Tables with new Fields
db.create_table(table_name='Exchange',
                storing_table=False,
                fields=('mean', float, 0.))
db.create_table(table_name='Data',
                storing_table=True,
                fields=[('array', ndarray), ('modified', bool, False)])


# Define an handler
def post_save_handler(table_name, data):
    print(f"Post-save signal received from {table_name} with data={data}")
    if data['mean'] < 0:
        db.update(table_name='Data',
                  data={'array': uniform(low=-1, high=1, size=(10,)),
                        'modified': True})


# Register and connect the handler
db.register_pre_save_signal(table_name='Exchange',
                            handler=post_save_handler)
db.connect_signals()


# Add a few lines
for _ in range(5):
    new_array = uniform(low=-1, high=1, size=(10,))
    db.add_data(table_name='Data',
                data={'array': new_array})
    db.add_data(table_name='Exchange',
                data={'mean': new_array.mean()})


# Check the Data Table content
print(db.get_lines(table_name='Data', batched=True))


# Close Database
db.close()
