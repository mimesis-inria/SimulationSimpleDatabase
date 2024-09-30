.. figure:: _static/images/logo.svg


SimulationSimpleDatabase
------------------------

The **SSD** project provides Python3 tools to easily develop a **storage** management system for **any synthetic data**
from **numerical simulations** with a minimal lines of code.

The project is mainly using the :Peewee:`Peewee <>` Python3 library and was mostly designed to fit the
:DeepPhysX:`DeepPhysX <>` and :SOFA:`SOFA <>` frameworks.


Features
--------

The **SSD** project provides the following features:

    .. table::
        :widths: 50 50
        :class: tight-table

        +------------------------------------------------------+------------------------------------------------------+
        | ``SSD.core``                                         | ``SSD.sofa``                                         |
        |  * Automatic management of Database file for any     |  * Same features as Core Storage package;            |
        |    data;                                             |  * Compatible layer with :SOFA:`SOFA <>` Python      |
        |  * Creation of customizable Tables in the Database;  |    bindings;                                         |
        |  * Easy writing and reading user interface;          |  * Callbacks to automatically record any Data field  |
        |  * Event management system;                          |    of SOFA objects.                                  |
        |  * Tools such as merging and exporting data in other |  * Recording can be done whether the simulation is   |
        |    formats.                                          |    running with ``runSofa`` or with a ``python``     |
        |                                                      |    interpreter.                                      |
        +------------------------------------------------------+------------------------------------------------------+


Gallery
-------

.. figure:: http://mimesis.inria.fr/wp-content/uploads/2022/10/gallery_caduceus.gif
    :align: center

    **examples/SOFA/rendering-offscreen/replay.py**


.. figure:: http://mimesis.inria.fr/wp-content/uploads/2022/10/gallery_liver.gif
    :align: center

    **examples/SOFA/rendering/replay.py**


.. toctree::
    :caption: PRESENTATION
    :maxdepth: 1
    :hidden:

    Install  <install.rst>
    About    <about.rst>


.. toctree::
    :caption: STORAGE
    :maxdepth: 1
    :hidden:

    Database             <core/database.rst>
    Table Relationships  <core/relationships.rst>
    Utils                <core/utils.rst>
    API                  <core/api.rst>


.. toctree::
    :caption: SOFA
    :maxdepth: 1
    :hidden:

    Storage    <sofa/storage.rst>
    API        <sofa/api.rst>