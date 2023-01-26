Visualizer
==========

Creating a Visualizer
---------------------

The *Visualizer* is managing the rendering of visual objects.
It uses *Actors* to create and update objects instances.
The visual data is received from a *Database*, thus it requires one to connect to.
The *Database* must obviously be the same for the *Factory* and the *Visualizer*.
There are several ways to create them, you can choose the more convenient regarding your applications:

.. code-block:: python

    from SSD.Core.Rendering.UserAPI import UserAPI
    from SSD.Core.Rendering.Visualizer import Visualizer

    # OPTION 1: Create a new Factory and launch the Visualizer from this Factory
    factory = UserAPI(database_dir='my_directory',
                      database_name='my_database',
                      remove_existing=True)
    factory.add_mesh(...)
    factory.launch_visualizer(backend='vedo')

    # OPTION 2: Create a new Factory and connect to a Visualizer manually
    factory = UserAPI(database_dir='my_directory',
                      database_name='my_database',
                      remove_existing=True)
    factory.add_mesh(...)
    Visualizer.launch(database_dir='my_directory',
                      database_name='my_database',
                      backend='vedo')
    factory.connect_visualizer()



.. warning::
    The *Visualizer* must be initialized **once all the object are added** to the *Factory*.


.. note::
    Several *Factories* can be connected to a single *Visualizer*.
    To do so, you must choose the option 2 with each call to ``factory.connect_visualizer`` done in a separate thread.


In both cases, several options are available when launching the *Visualizer*:

.. list-table::
    :width: 100%
    :widths: 15 10 75
    :header-rows: 1
    :class: tight-table

    * - Field
      - Type
      - Description

    * - ``backend``
      - :guilabel:`str`
      - The name of the *Visualizer* to use (either ``vedo`` or ``open3d``).

    * - ``offscreen``
      - :guilabel:`bool`
      - If True, the visualization will be done offscreen.

    * - ``fps``
      - :guilabel:`int`
      - Maximum frame rate.


Updating a Visualizer
---------------------

The *Visualizer* updates the rendering view when a call to ``render`` is triggered in the *Factory.
Between two calls of the ``render`` method, visual object data can be updated several times per object.
If an object was not updated during the step, an empty line is added to the corresponding *Table* in the *Database*
to keep the same number of rows in all *Tables*.

.. code-block:: python

    factory.update_mesh(...)
    factory.update_points(...)
    factory.render()


.. warning::
    Do not forget to close the *Visualizer* at the end of of your simulation:

    .. code-block:: python

        factor.close()


Replay Visualizer
-----------------

Once a *Database* with visual data is recorded, it is possible to replay it using the *ReplayVisualizer*.
It will read a row of all *Tables* at each time step (this is one of the reasons why we want to keep the *Tables*
synchronized with ont row per step).
The *ReplayVisualizer* only requires to be initialized to be launched:

.. code-block:: python

    from SSD.Core.Rendering.Replay import Replay

    # Launch the ReplayVisualizer
    Replay(database_dir='my_directory',
           database_name='my_database',
           backend='open3d').launch()


.. note::
    It is totally possible to use the ``open3D`` backend with a *Database* previously used with ``vedo`` and vice-versa.