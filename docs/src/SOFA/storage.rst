SOFA Storage
============

Specificity
-----------

The **SSD** project provides a compatible *Database* with :SOFA:`SOFA <>` framework.
There are two main advantages with this specialized *Database*:

 * the recording can be launched whether the simulation is driven by the :SOFA:`SOFA <>` GUI or by a Python
   interpreter;
 * callbacks can be defined to record automatically Data fields of SOFA components.


.. note::
    The SOFA version of the *Database* is able to record data at each time step since it inherits from
    :guilabel:`Sofa.Core.Controller`. The event corresponding to the end of the time step is therefore caught and
    triggers access to the recorded Data fields.


Record Data fields
------------------

The way to create such a *Database* is slightly different than in the ``Core`` version.
In fact, the *Database* is considered as a SOFA component and must be added to the scene graph.
Only the root node of the scene graph should be given, the *Database* will then create its own child node and add
itself to the graph.

Adding callbacks is very simple, since you only have to specify:

 * the *Table* and the *Field* to use in the *Database*;
 * the absolute path to the SOFA component in the scene graph and the name of th e Data field to record.

.. tabs::

    .. tab:: Python Interpreter

        .. code-block:: python

            import Sofa
            from SSD.SOFA.Storage import Database

            # Create the root node
            root = Sofa.Core.Node('root')
            root.addObject('RequiredPlugin', pluginName=['SofaOpenglVisual', 'SofaNonUniformFem', 'SofaLoader', 'SofaConstraint',
                                                         'SofaImplicitOdeSolver', 'SofaMeshCollision', 'SofaSimpleFem'])

            # Create a falling ball
            root.addChild('ball')
            root.ball.addObject('EulerImplicitSolver')
            root.ball.addObject('CGLinearSolver')
            root.ball.addObject('MechanicalObject', name='BallMO', template='Rigid3')
            root.ball.addObject('UniformMass', totalMass=1.)

            # Add a visual model
            root.ball.addChild('visual')
            root.ball.visual.addObject('MeshObjLoader', name='Loader', filename='mesh/ball.obj')
            root.ball.visual.addObject('OglModel', name='BallOGL', src='@Loader')
            root.ball.visual.addObject('RigidMapping', input='@..', output='@.')

            # Create a new Database
            database = Database(root=root, database_name='ball').new(remove_existing=True)
            database.create_table(table_name='Ball')
            database.add_callback(table_name='Ball', field_name='center',
                                  record_object='@ball.BallMO', record_field='position')
            database.add_callback(table_name='Ball', field_name='positions',
                                  record_object='@ball.visual.BallOGL', record_field='position')

            # Init the scene graph and run some step of the simulation
            Sofa.Simulation.init(root)
            for _ in range(10):
                Sofa.Simulation.animate(root, root.dt.value)


    .. tab:: SOFA GUI

        .. code-block:: python

            from SSD.SOFA.Storage import Database

            def createScene(root):

                # Create a falling ball
                root.addChild('ball')
                root.ball.addObject('EulerImplicitSolver')
                root.ball.addObject('CGLinearSolver')
                root.ball.addObject('MechanicalObject', name='BallMO', template='Rigid3')
                root.ball.addObject('UniformMass', totalMass=1.)

                # Add a visual model
                root.ball.addChild('visual')
                root.ball.visual.addObject('MeshObjLoader', name='Loader', filename='mesh/ball.obj')
                root.ball.visual.addObject('OglModel', name='BallOGL', src='@Loader')
                root.ball.visual.addObject('RigidMapping', input='@..', output='@.')

                # Create a new Database & record some Data fields
                database = Database(root=root, database_name='ball').new(remove_existing=True)
                database.create_table(table_name='Ball')
                database.add_callback(table_name='Ball', field_name='center',
                                      record_object='@ball.BallMO', record_field='position')
                database.add_callback(table_name='Ball', field_name='positions',
                                      record_object='@ball.visual.BallOGL', record_field='position')


.. hint::
    Only raw data of Data fields can be recorded with such a method.
    However, you can still use the ``SDD.Core`` API of the *Database* to "manually" insert data.
    If you write your scene as a :guilabel:`Sofa.Core.Controller`, you will be able to process these data operation
    with event handlers (such as ``onAnimateBeginEvent`` or ``onAnimateEndEvent``).

    Example: **/example/SOFA/storage/record.py**
