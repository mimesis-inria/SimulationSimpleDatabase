Visualizer
==========

Creating a Visualizer
---------------------

The *Visualizer* is managing the rendering of visual objects.
It uses *Actors* to create and update objects instances.
The visual data is received from a *Database*, thus it requires one to connect to (it can either be an existing one
either create a new one by itself).
The *Database* must obviously be the same for the *Factory* and the *Visualizer*, you can access the *Database* of one
of them using the ``get_database`` method.
There are several ways to create them, you can choose the more convenient regarding your applications:

.. code-block:: python

    from SSD.Core.Storage.Database import Database
    from SSD.Core.Rendering.Factory import Factory
    from SSD.Core.Rendering.Visualizer import Visualizer

    # Create a new Database then a new Factory and a new Visualizer
    db = Database(database_dir='my_directory',
                  database_name='my_database').new(remove_existing=True)
    factory = Factory(database=db)
    visualizer = Visualizer(database=db)

    # Create only a new Factory (the Database will be automatically created) and then a new Visualizer
    factory = Factory(database_dir='my_directory',
                      database_name='my_database',
                      remove_existing=True)
    visualizer = Visualizer(database=factory.get_database())

    # Create only a new Visualizer (the Database will be automatically created) and then a new Factory
    visualizer = Visualizer(database_dir='my_directory',
                            database_name='my_database',
                            remove_existing=True)
    factory = Factory(database=factory.get_database())


Initializing a Visualizer
-------------------------

The *Visualizer* must be initialized **once all the object are added** to the *Factory*:

.. code-block:: python

    # Add objects to the Factory
    factory.add_mesh(...)
    factory.add_points(...)

    # Render them in the Visualizer
    visualize.init_visualizer()


The rendering window should the appear with a "start" button.
You can interact with the objects to place the camera in the desired position, since the interactions will be disabled
during the execution of your code (otherwise the rendering window will stay master and you following code will not be
executed).
Once you press the "start" button, interactions are disabled and the next part of the code is executed.


Updating a Visualizer
---------------------

The *Visualizer* only updates the rendering view when a call to ``render`` is triggered.
This method can either be called from the *Visualizer* itself or from the *Factory* since both components are connected
to a signal that trigger a synchronization:

 * in the *Factory*, a new row can be edited in all *Tables*;
 * in the *Visualizer*, all instances are updated; if a *Table* was not edited for this step, an empty line is added to
   keep the same number of rows in all *Tables*.

.. code-block:: python

    # Update objects and render from the Visualizer
    factory.update_mesh(...)
    factory.update_points(...)
    visualizer.render()

    # Update objects and render from the Factory
    factory.update_mesh(...)
    factory.update_points(...)
    factory.render()


Replay Visualizer
-----------------

Once a *Database* with visual data is recorded, it is possible to replay it using the *ReplayVisualizer*.
It will read a row of all *Tables* at each time step (this is one of the reasons why we want to keep the *Tables*
synchronized with ont row per step).
The *ReplayVisualizer* only requires to be initialized to be launched:

.. code-block:: python

    from SSD.Core.Rendering.ReplayVisualizer import ReplayVisualizer

    # Launch the ReplayVisualizer
    visualizer = ReplayVisualizer(database_dir='my_directory',
                                  database_name='my_database')
    visualizer.init_visualizer()
