Database
========

Creating a Database
-------------------

The *Database* will store its *Tables* in a single file which name and directory must be specified.
To create this file with a `.db` extension, a call to the ``new`` method is required:

.. code-block:: python

    from SSD.Core import Database

    # Create a new Database object and a new storage file
    db = Database(database_dir='my_directory',
                  database_name='my_database')
    db.new(remove_existing=True)

    # Same thing in a single line
    db = Database(database_dir='my_directory',
                  database_name='my_database').new(remove_existing=True)


Loading a Database
------------------

Loading an existing *Database* is pretty similar as creating a new one, except the call to the ``load`` method:

.. code-block:: python

    from SSD.Core import Database

    # Create a new Database object and load an exiting storage file
    db = Database(database_dir='my_directory',
                  database_name='my_database')
    db.load(show_architecture=True)

    # Same thing in a single line
    db = Database(database_dir='my_directory',
                  database_name='my_database').load(show_architecture=True)


Creating a new Table
--------------------

Creating a new *Table* to the *Database* only requires its name and the type (either *StoringTable* or *ExchangeTable*):

.. code-block:: python

    # Create a StoringTable
    db.create_table(table_name='my_StoringTable',
                    storing_table=True)

    # Create an ExchangeTable
    db.create_table(table_name='my_ExchangeTable',
                    storing_table=False)


Creating a new Field
--------------------

Creating a new *Field* requires a few information in a tuple defined as
:guilabel:`(field_name, field_type, default_value)`.
The default value specifies the value to set in a row if an entry does not contain data for this field.
The name and the type of the *Field* are mandatory but the default value is optional; if not set, it will be ``<null>``.

*Fields* can either be created one by one or at once:

.. code-block:: python

    # Create several Fields in the StoringTable
    db.create_fields(table_name='my_StoringTable',
                     fields=[('my_Value', float, 0.), ('my_Condition', bool, False), ('my_Color', str)])

    # Create a unique Field in the ExchangeTable
    db.create_fields(table_name='my_ExchangeTable',
                     fields=('my_Data', float, 0.))

It is also possible to create fields at *Table* creation:

.. code-block:: python

    # Create a StoringTable with several fields
    db.create_table(table_name='my_StoringTable',
                    storing_table=True,
                    fields=[('my_Value', float, 0.), ('my_Condition', bool, False), ('my_Color', str)])

    # Create an ExchangeTable with a unique field
    db.create_table(table_name='my_ExchangeTable',
                    storing_table=False,
                    fields=('my_Data', float, 0.))


The following *Field* types are available:

.. table::
    :widths: 10 15 20

    +--------------+--------------------------------------+---------------------------------------------------------------------------------------+
    | **Type**     | **Definition**                       | **Field Documentation**                                                               |
    +==============+======================================+=======================================================================================+
    | ``int``      | :guilabel:`int`                      | `IntegerField <http://docs.peewee-orm.com/en/latest/peewee/api.html#IntegerField>`_   |
    +--------------+--------------------------------------+---------------------------------------------------------------------------------------+
    | ``float``    | :guilabel:`float`                    | `FloatField <http://docs.peewee-orm.com/en/latest/peewee/api.html#FloatField>`_       |
    +--------------+--------------------------------------+---------------------------------------------------------------------------------------+
    | ``str``      | :guilabel:`str`                      | `TextField <http://docs.peewee-orm.com/en/latest/peewee/api.html#TextField>`_         |
    +--------------+--------------------------------------+---------------------------------------------------------------------------------------+
    | ``bool``     | :guilabel:`bool`                     | `BooleanField <http://docs.peewee-orm.com/en/latest/peewee/api.html#BooleanField>`_   |
    +--------------+--------------------------------------+---------------------------------------------------------------------------------------+
    | ``ndarray``  | :guilabel:`import numpy.ndarray`     | See ``AdaptiveDB/ExtendedFields.py``                                                  |
    +--------------+--------------------------------------+---------------------------------------------------------------------------------------+
    | ``datetime`` | :guilabel:`import datetime.datetime` | `DateTimeField <http://docs.peewee-orm.com/en/latest/peewee/api.html#DateTimeField>`_ |
    +--------------+--------------------------------------+---------------------------------------------------------------------------------------+


Adding data to a Table
----------------------

Adding data to a *Table* can be done either line by line either per batch of lines.
In both cases, data must be passed as a dictionary and the index of the created line(s) are returned:

.. code-block:: python

    # Add a batch to the StoringTable
    db.add_batch(table_name='my_StoringTable',
                 batch={'my_Value': [7.4, 5.6, -2.1],
                        'my_Condition': [True, True, False],
                        'my_Color': ['red', 'orange', 'blue']})

    # Add a single line to the ExchangeTable
    db.add_data(table_name='my_ExchangeTable',
                data={'my_Data': 0.5})


Updating data in a Table
------------------------

Updating data is also possible and can be only performed line by line.
The index of the line can be specified (index can be negative to count from the last line).
By default, the last entry will be updated.
The data still needs to be passed as a dictionary, only specified *Fields* will be updated.

.. code-block:: python

    # Update the 3rd line of the StoringTable
    db.update(table_name='my_StoringTable',
              line_id=3,
              data={'my_Value': 1.3,
                    'my_Color': 'green'})

    # Update the last line of the StoringTable
    db.update(table_name='my_StoringTable',
              line_id=-1,
              data={'my_Value': -1.9})


Getting data from a Table
-------------------------

Getting data from a *Table* can be done either line by line either per batch of lines.
By default, all fields are received but a selection can be specified.
With ``get_line`` method, the index of the line can be specified; by default, the last line is selected.
With ``get_lines`` method, a set of lines can be specified; if this set of lines is not specified, a range of lines can
be specified; by default, the whole set of lines is selected.
In both cases, data is received as a dictionary:

.. code-block:: python

    # Get a batch from the StoringTable
    db.get_lines(table_name='my_StoringTable',
                 fields=['my_Value', 'my_Color'],
                 lines_range=[1, -1],
                 batched=True)
    """
    >> {'my_Value': [7.4, 5.6, -2.1],
        'my_Condition': [True, True, False],
        'my_Color': ['red', 'orange', 'blue']}
    """

    # Get a line from the ExchangeTable
    db.get_line(table_name='my_ExchangeTable'
                fields='my_Data',
                line_id=1)
    """
    >> {'my_Data': 0.5}
    """


Connecting Signals
------------------

*Tables* can send two types of signals when data is added: a ``pre_save_signal`` and a ``post_save_signal``.
Signal handler can be connected to these signals by the *Database*.
When data is added to a *Table*, the registered handlers are triggered in the registration order (just before or just
after the data insert depending on the signal type).
Signals must be registered and connected when initializing the *Database*:

.. code-block:: python

    # Create a new Database
    db = Database(database_dir='my_directory',
                  database_name='my_database').new(remove_existing=True)
    # Create an ExchangeTable with one Field
    db.create_fields(table_name='my_ExchangeTable',
                     fields=('my_Data', float, 0.))

    # Define handlers
    def pre_save_handler(table_name, data):
        print(f"Pre-save signal received from {table_name}")

    def post_save_handler(table_name, data):
        print(f"Post-save signal received from {table_name} with data={data}")

    # Register signals
    db.register_pre_save_signal(table_name='my_ExchangeTable',
                                handler=pre_save_handler)
    db.register_post_save_signal(table_name='my_ExchangeTable',
                                 handler=post_save_handler)

    # Connect signals once they are all registered
    db.connect_signals()

    # Adding data to the Table
    db.add_data(table_name='my_ExchangeTable',
                data={'my_Data': 0.5})
    """
    >> Pre-save signal received from my_ExchangeTable
    >> Post-save signal received from my_ExchangeTable with data={'my_Data': 0.5}
    """
