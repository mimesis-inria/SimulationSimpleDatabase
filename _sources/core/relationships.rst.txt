Table Relationship
==================

Creating a relation between Tables
----------------------------------

The *Database* also manages the relations between *Tables*.
This way, a *Field* can refer to another *Table*; this *Field* actually contains the index of a row instance in that
*Table*.

To create a relationship between *Tables*, the first *Table* must be created, then specified as *Field* type when
creating the second *Table*:

.. code-block:: python

    # Create the first Table
    db.create_table(table_name='Stats',
                    fields=[('mean', float, 0.), ('max', float, 0.)])
    db.create_table(table_name='Arrays',
                    fields=[('array', ndarray), ('stats', 'Stats')])
    db.print_architecture()
    """
    >> DATABASE database.db
         * StoringTable 'Stats'
            - id (AUTO) (default)
            - mean (FLOAT)
            - max (FLOAT)
         * StoringTable 'Arrays'
            - id (AUTO) (default)
            - array (NUMPY)
            - stats (FK -> Stats)
    """


Adding data to joined Tables
----------------------------

Adding data to joined *Tables* can be done independently, but you may find it more convenient to do that only using the
main *Table*.
Data can still be added either line by line either per batch of lines:

.. code-block:: python

    new_array = np.random.uniform(size=(10,))

    # Add a single line to Tables independently
    id_stats_line = db.add_data(table_name='Stats',
                                data={'mean': new_array.mean(),
                                      'max':  new_array.max()})
    db.add_data(table_name='Arrays',
                data={'array': new_array,
                      'stats': id_stats_line})

    # Add a single line to Tables using the main Table
    db.add_data(table_name='Arrays',
                data={'array': new_array,
                      'stats': {'mean': new_array.mean(),
                                'max':  new_array.max()}})

.. code-block:: python

    new_arrays = [np.random.uniform(size=(10,)) for _ in range(5)]

    # Add a batch to Tables independently
    id_stats_lines = db.add_batch(table_name='Stats',
                                  data={'mean': [new_array.mean() for new_array in new_arrays],
                                        'max':  [new_array.max() for new_array in new_arrays]})
    db.add_batch(table_name='Arrays',
                 batch={'array': new_arrays,
                        'stats': id_stats_lines})

    # Add a batch to Tables using th main Table
    db.add_batch(table_name='Arrays',
                 batch={'array': new_arrays,
                        'stats': {'mean': [new_array.mean() for new_array in new_arrays],
                                  'max':  [new_array.max()  for new_array in new_arrays]}})



Updating data in joined Tables
------------------------------

Updating data in joined *Tables* can be done independently, but you may find it more convenient to do that only using
the main *Table*.
Data updates can only be performed line by line:

.. code-block:: python

    new_array = np.random.uniform(size=(10,))

    # Update a line in Tables independently
    array_data = db.get_line(table_name='Arrays',
                             line_id=1,
                             fields='stats')
    db.update(table_name='Arrays',
              line_id=1,
              data={'array': new_array})
    db.update(table_name='Stats',
              line_id=array_data['stats'],
              data={'mean': new_array.mean(),
                    'max':  new_array.max()})

    # Update a line in Tables using the main Table
    db.update(table_name='Arrays',
              line_id=1,
              data={'array': new_array,
                    'stats': {'mean': new_array.mean(),
                              'max':  new_array.max()}})


Getting data from joined Tables
-------------------------------

Getting data from joined *Tables* can be done independently, but you may find it more convenient to do that only using
the main *Table*.
Data can still be accessed either line by line either per batch of lines:

.. code-block:: python

    # Get a single line from Tables independently
    array_data = db.get_line(table_name='Arrays',
                             line_id=1)
    stats_data = db.get_line(table_name='Stats',
                             line_id=array_data['stats'])
    """
    >> array_data = {'id': 1,
                     'array': array(...),
                     'stats': 1}
       stats_data = {'id': 1,
                     'mean': 0.23,
                     'max': 0.41}
    """

    # Get a single line from Tables using the main Table
    array_data = db.get_line(table_name='Arrays',
                             line_id=1,
                             joins='Stats')
    """
    >> array_data = {'id': 1,
                     'array': array(...),
                     'stats': {'id': 1,
                               'mean': 0.23,
                               'max': 0.41}}
    """

.. code-block:: python

    # Get a batch from Tables independently
    array_data = db.get_lines(table_name='Arrays',
                              lines_range=[1, 3],
                              batched=True)
    stats_data = db.get_lines(table_name='Stats',
                              lines_id=array_data['stats'],
                              batched=True)
    """
    >> array_data = {'id': [1, 2, 3],
                     'array': [array(...), array(...), array(...)]
                     'stats': [1, 2, 3]}
       stats_data = {'id': [1, 2, 3],
                     'mean': [0.23, 0.56, 0.47],
                     'max': [0.41, 0.82, 0.64]}
    """

    # Get a batch from Tables using the main Table
    array_data = db.get_lines(table_name='Arrays',
                              lines_range=[1, 3],
                              batched=True)
    """
    >> array_data = {'id': [1, 2, 3],
                     'array': [array(...), array(...), array(...)]
                     'stats': {'id': [1, 2, 3],
                               'mean': [0.23, 0.56, 0.47],
                               'max': [0.41, 0.82, 0.64]}}
    """
