Factory
=======

Creating a Factory
------------------

The *Factory* is an easy user interface to create and update visual objects such as meshes, point-clouds, etc.
The *Factory* will also automatically store each object in a dedicated *Table* of a *Database*.
Thus, it requires a *Database* to connect to (it can either be an existing one either create a new one by itself):

.. code-block:: python

    from SSD.Core.Storage.Database import Database
    from SSD.Core.Rendering.Factory import Factory

    # Create a new Database then a new Factory
    db = Database(database_dir='my_directory',
                  database_name='my_database').new(remove_existing=True)
    factory = Factory(database=db)

    # Create only a new Factory (the Database will be automatically created)
    factory = Factory(database_dir='my_directory',
                      database_name='my_database',
                      remove_existing=True)


Adding an object to the Factory
-------------------------------

The *Factory* provides a specific method to create each of the available objects with ``add_<object>``.
These methods allow to highly customize the objects rendering style.
Each object will have a unique identifier in the factory, following the order of creation:

.. code-block:: python

    # Adding a mesh
    idx = factory.add_mesh(positions=position_array,
                           cells=cells_array)
    print(idx)
    """
    >> 0
    """

    # Adding a point-cloud
    idx = factory.add_points(positions=position_array)
    print(idx)
    """
    >> 1
    """


Updating an object in the Factory
---------------------------------

The *Factory* also provides a specific method to update each of the available objects with ``update_<object>``.
Object state and some rendering options can be updated depending on the object.
It is important to specify the right identifier in the factory (identifiers follow the order of creation):

.. code-block:: python

    # Updating a mesh
    factory.update_mesh(object_id=0,
                        positions=updated_position_array)

    # Updating a point-cloud
    factory.update_points(object_id=1,
                          positions=updated_position_array)


.. note::

    You can update a single object several times per time step, meaning that the same raw of data in the *Table* will
    be modified.
    A call to ``render`` will synchronize *Tables* and a new row will be edited next (see Visualizer).

VedoFactory
-----------

The *VedoFactory* allows to create :Vedo:`Vedo <>` visual objects.
The available objects are:
:VedoObject:`Mesh <mesh.html#vedo.mesh.Mesh>`,
:VedoObject:`Points <pointcloud.html#vedo.pointcloud.Points>`,
:VedoObject:`Arrows <shapes.html#vedo.shapes.Arrows>`,
:VedoObject:`Markers <shapes.html#vedo.shapes.Marker>`,
:VedoObject:`Symbols <shapes.html#vedo.shapes.Glyph>`

Mesh
""""

.. list-table::
    :width: 100%
    :widths: 15 10 10 10 55
    :header-rows: 1
    :class: tight-table

    * - Field
      - Type
      - Init
      - Update
      - Description

    * - ``positions``
      - :guilabel:`ndarray`
      - **Required**
      - Optional
      - List of vertices. Updated position vector must always have the same size.

    * - ``cells``
      - :guilabel:`ndarray`
      - **Required**
      - *Disabled*
      - List of connections between vertices.

    * - ``at``
      - :guilabel:`int`
      - Optional
      - *Disabled*
      - Sub-window in which the *Mesh* will be rendered.

    * - ``alpha``
      - :guilabel:`float`
      - Optional
      - Optional
      - Opacity of the *Mesh* between 0 and 1.

    * - ``c``
      - :guilabel:`str`
      - Optional
      - Optional
      - Uniform color of the *Mesh*.

    * - ``colormap``
      - :guilabel:`str`
      - Optional
      - *Disabled*
      - Name of the color palette that maps a color to a scalar value.

    * - ``scalar_field``
      - :guilabel:`ndarray`
      - Optional
      - Optional
      - List of scalar values to define color based on the colormap.

    * - ``wireframe``
      - :guilabel:`bool`
      - Optional
      - Optional
      - Specifies if the *Mesh* should be rendered as wireframe.

    * - ``compute_normals``
      - :guilabel:`bool`
      - Optional
      - *Disabled*
      - Specifies if the normals of the *Mesh* should be re-computed.

    * - ``line_width``
      - :guilabel:`float`
      - Optional
      - *Disabled*
      - Width of the edges.

.. admonition:: Example

    See example in ``examples/Core/Rendering/mesh.py``.

    .. figure:: ../../_static/image/vedo_visualizer_mesh.png
        :alt: vedo_visualizer_mesh.png
        :width: 30%

Points
""""""

.. list-table::
    :width: 100%
    :widths: 15 10 10 10 55
    :header-rows: 1
    :class: tight-table

    * - Field
      - Type
      - Init
      - Update
      - Description

    * - ``positions``
      - :guilabel:`ndarray`
      - **Required**
      - Optional
      - List of vertices. Updated position vector must always have the same size.

    * - ``at``
      - :guilabel:`int`
      - Optional
      - *Disabled*
      - Sub-window in which the *Points* will be rendered.

    * - ``alpha``
      - :guilabel:`float`
      - Optional
      - Optional
      - Opacity of the *Points* between 0 and 1.

    * - ``c``
      - :guilabel:`str`
      - Optional
      - Optional
      - Uniform color of the *Points*.

    * - ``colormap``
      - :guilabel:`str`
      - Optional
      - *Disabled*
      - Name of the color palette that maps a color to a scalar value.

    * - ``scalar_field``
      - :guilabel:`ndarray`
      - Optional
      - Optional
      - List of scalar values to define color based on the colormap.

    * - ``point_size``
      - :guilabel:`float`
      - Optional
      - Optional
      - Size of the *Points*.

.. admonition:: Example

    See example in ``examples/Core/Rendering/points.py``.

    .. figure:: ../../_static/image/vedo_visualizer_points.png
        :alt: vedo_visualizer_points.png
        :width: 30%

Arrows
""""""

.. list-table::
    :width: 100%
    :widths: 15 10 10 10 55
    :header-rows: 1
    :class: tight-table

    * - Field
      - Type
      - Init
      - Update
      - Description

    * - ``positions``
      - :guilabel:`ndarray`
      - **Required**
      - Optional
      - List of starting positions of the *Arrows*.

    * - ``vectors``
      - :guilabel:`ndarray`
      - **Required**
      - Optional
      - List of vectors defining the *Arrows*.

    * - ``at``
      - :guilabel:`int`
      - Optional
      - *Disabled*
      - Sub-window in which the *Arrows* will be rendered.

    * - ``alpha``
      - :guilabel:`float`
      - Optional
      - Optional
      - Opacity of the *Arrows* between 0 and 1.

    * - ``c``
      - :guilabel:`str`
      - Optional
      - Optional
      - Uniform color of the *Arrows*.

    * - ``colormap``
      - :guilabel:`str`
      - Optional
      - *Disabled*
      - Name of the color palette that maps a color to a scalar value.

    * - ``scalar_field``
      - :guilabel:`ndarray`
      - Optional
      - Optional
      - List of scalar values to define color based on the colormap.

    * - ``res``
      - :guilabel:`int`
      - Optional
      - Optional
      - Circular resolution of the *Arrows*.

.. admonition:: Example

    See example in ``examples/Core/Rendering/arrows.py``.

    .. figure:: ../../_static/image/vedo_visualizer_arrows.png
        :alt: vedo_visualizer_arrows.png
        :width: 30%

Markers
"""""""

.. list-table::
    :width: 100%
    :widths: 15 10 10 10 55
    :header-rows: 1
    :class: tight-table

    * - Field
      - Type
      - Init
      - Update
      - Description

    * - ``normal_to``
      - :guilabel:`int`
      - **Required**
      - Optional
      - Index of the object in the *Factory* on which the *Markers* will be rendered (*Mesh* or *Points*).

    * - ``indices``
      - :guilabel:`ndarray`
      - **Required**
      - Optional
      - Indices of the vertices on which the *Markers* will be rendered.

    * - ``at``
      - :guilabel:`int`
      - Optional
      - *Disabled*
      - Sub-window in which the *Markers* will be rendered.

    * - ``alpha``
      - :guilabel:`float`
      - Optional
      - Optional
      - Opacity of the *Markers* between 0 and 1.

    * - ``c``
      - :guilabel:`str`
      - Optional
      - Optional
      - Uniform color of the *Markers*.

    * - ``colormap``
      - :guilabel:`str`
      - Optional
      - *Disabled*
      - Name of the color palette that maps a color to a scalar value.

    * - ``scalar_field``
      - :guilabel:`ndarray`
      - Optional
      - Optional
      - List of scalar values to define color based on the colormap.

    * - ``symbol``
      - :guilabel:`str`
      - Optional
      - Optional
      - Symbol of the *Markers*.

    * - ``size``
      - :guilabel:`float`
      - Optional
      - Optional
      - Size of the *Markers*.

    * - ``filled``
      - :guilabel:`bool`
      - Optional
      - Optional
      - Specifies whether the symbols should be filled or not.

.. admonition:: Example

    See example in ``examples/Core/Rendering/markers.py``.

    .. figure:: ../../_static/image/vedo_visualizer_markers.png
        :alt: vedo_visualizer_markers.png
        :width: 30%

Symbols
"""""""

.. list-table::
    :width: 100%
    :widths: 15 10 10 10 55
    :header-rows: 1
    :class: tight-table

    * - Field
      - Type
      - Init
      - Update
      - Description

    * - ``positions``
      - :guilabel:`ndarray`
      - **Required**
      - Optional
      - List of positions of the *Symbols*.

    * - ``orientations``
      - :guilabel:`ndarray`
      - **Required**
      - Optional
      - Orientations of the *Symbols*. Can be a same orientation vector for all or an orientation vector per symbol.

    * - ``at``
      - :guilabel:`int`
      - Optional
      - *Disabled*
      - Sub-window in which the *Symbols* will be rendered.

    * - ``alpha``
      - :guilabel:`float`
      - Optional
      - Optional
      - Opacity of the *Symbols* between 0 and 1.

    * - ``c``
      - :guilabel:`str`
      - Optional
      - Optional
      - Uniform color of the *Symbols*.

    * - ``colormap``
      - :guilabel:`str`
      - Optional
      - *Disabled*
      - Name of the color palette that maps a color to a scalar value.

    * - ``scalar_field``
      - :guilabel:`ndarray`
      - Optional
      - Optional
      - List of scalar values to define color based on the colormap.

    * - ``symbol``
      - :guilabel:`str`
      - Optional
      - Optional
      - Symbol of the *Symbols*.

    * - ``size``
      - :guilabel:`float`
      - Optional
      - Optional
      - Size of the *Symbols*.

    * - ``filled``
      - :guilabel:`bool`
      - Optional
      - Optional
      - Specifies whether the symbols should be filled or not.

.. admonition:: Example

    See example in ``examples/Core/Rendering/markers.py``.

    .. figure:: ../../_static/image/vedo_visualizer_symbols.png
        :alt: vedo_visualizer_symbols.png
        :width: 30%
