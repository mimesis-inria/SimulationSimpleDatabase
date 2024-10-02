Utils
=====

Merging Databases
-----------------

The ``merge`` tool allows users to merge existing *Databases* in a new *Database*.
Each *Table* from all *Databases* will be duplicated in the new *Database*; in the case where *Databases* share a common
*Table* name, *Tables* will be merged in the logical order.

.. code-block:: python

    from SSD.core import merge

    merge(database_files=['my_Database1', 'my_Database2'],
          new_database_file='my_MergedDatabase',
          remove_existing=True)
    """
    >> DATABASE my_Database1.db
         * StoringTable 'my_StoringTable'
            - id (AUTO) (default)
            - my_Value (FLOAT)
            - my_Condition (BOOL)
         * ExchangeTable 'my_ExchangeTable'
            - id (AUTO) (default)
            - _dt_ (DATETIME) (default)
            - my_Data (FLOAT)

    >> DATABASE my_Database2.db
         * StoringTable 'my_StoringTable'
            - id (AUTO) (default)
            - my_Value (FLOAT)
            - my_Color (TEXT)
         * ExchangeTable 'my_OtherExchangeTable'
            - id (AUTO) (default)
            - _dt_ (DATETIME) (default)
            - my_Data (FLOAT)

    >> DATABASE my_MergedDatabase.db
         * StoringTable 'my_StoringTable'
            - id (AUTO) (default)
            - my_Value (FLOAT)
            - my_Condition (BOOL)
            - my_Color (TEXT)
         * ExchangeTable 'my_ExchangeTable'
            - id (AUTO) (default)
            - _dt_ (DATETIME) (default)
            - my_Data (FLOAT)
         * ExchangeTable 'my_OtherExchangeTable'
            - id (AUTO) (default)
            - _dt_ (DATETIME) (default)
            - my_Data (FLOAT)

    >> Confirm new Database architecture ? (y/n): y
    Proceeding...
    Merge complete.
    """


Renaming Tables and Fields
--------------------------

The ``rename_tables`` and ``rename_fields`` tools allows users to rename *Tables* and *Fields* in the *Database*.
Both methods require tuples defines as :guilabel:`(current_name, new_name)`:

.. code-block:: python

    from SSD.core import rename_tables, rename_fields

    rename_tables(database_file='my_Database',
                  renamed_tables=[('my_StoringTable', 'my_NewStoringTable'), ('my_ExchangeTable', 'my_NewExchangeTable')])
    """
    >> DATABASE my_Database.db
         * StoringTable 'my_NewStoringTable'
            - id (AUTO) (default)
            - my_Value (FLOAT)
            - my_Condition (BOOL)
            - my_Color (TEXT)
         * ExchangeTable 'my_NewExchangeTable'
            - id (AUTO) (default)
            - _dt_ (DATETIME) (default)
            - my_Data (FLOAT)
    """

    rename_fields(database_file='my_Database',
                  table_name='my_NewStoringTable',
                  renamed_fields=('my_Condition', 'my_Test'))
    """
    >> DATABASE my_Database.db
         * StoringTable 'my_NewStoringTable'
            - id (AUTO) (default)
            - my_Value (FLOAT)
            - my_Test (BOOL)
            - my_Color (TEXT)
         * ExchangeTable 'my_NewExchangeTable'
            - id (AUTO) (default)
            - _dt_ (DATETIME) (default)
            - my_Data (FLOAT)
    """


Removing Tables and Fields
--------------------------

The ``remove_tables`` and ``remove_fields`` tools allows users to remove *Tables* and *Fields* from a *Database*.

.. code-block:: python

    from SSD.core import remove_tables, remove_fields

    rename_tables(database_name='my_Database',
                  remove_tables='my_ExchangeTable')
    """
    >> DATABASE my_Database.db
         * StoringTable 'my_NewStoringTable'
            - id (AUTO) (default)
            - my_Value (FLOAT)
            - my_Condition (BOOL)
            - my_Color (TEXT)
    """

    remove_fields(database_name='my_Database',
                  table_name='my_StoringTable',
                  remove_fields=['my_Condition', 'my_Color'])
    """
    >> DATABASE my_Database.db
         * StoringTable 'my_NewStoringTable'
            - id (AUTO) (default)
            - my_Value (FLOAT)
    """


Exporting Databases
-------------------

The ``export`` tool allows users to export a *Database* either in CSV format either in JSON format:

.. code-block:: python

    from SSD.core import export

    export(database_name='my_Database',
           exporter='csv',
           filename='my_db_export',
           remove_existing=True)
    """
    >> Exported my_db_export.csv
    """

    export(database_name='my_Database',
           exporter='json',
           filename='my_db_export',
           remove_existing=True)
    """
    >> Exported my_db_export.json
    """