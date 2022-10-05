.. figure:: _static/images/logo.svg


SSD - SimulationSimpleDatabase
------------------------------

The **SSD** project provides Python3 tools allowing users to easily develop **data storage** strategies for their
**numerical simulations**.

This project has two main objectives:

    .. table::
        :widths: 15 90

        +---------------+------------------------------------------------------------------------------------------+
        | ``Storage``   | Easy **storage** management system for **any data** from a numerical simulation.         |
        +---------------+------------------------------------------------------------------------------------------+
        | ``Rendering`` | Easy **storage** & **rendering** management systems for **visual data** from a numerical |
        |               | simulation.                                                                              |
        +---------------+------------------------------------------------------------------------------------------+



The **SSD** project is mainly using the :Peewee:`Peewee <>` Python3 library and was mostly designed to fit the
:DeepPhysX:`DeepPhysX <>` and :SOFA:`SOFA <>` frameworks.


Features
--------

The **SSD** project provides the following packages:

    .. table::
        :widths: 50 50
        :class: tight-table

        +------------------------------------------------------+------------------------------------------------------+
        | ``SSD.Core.Storage``                                 | ``SSD.Core.Rendering``                               |
        |  * Automatic management of Database file for any     |  * Automatic management of Database file for         |
        |    data;                                             |    visualization data;                               |
        |  * Creation of highly customizable Tables in the     |  * Live rendering of numerical simulations;          |
        |    Database;                                         |  * Replay of stored numerical simulation steps;      |
        |  * Easy writing and reading user interface;          |  * Various object types and highly customizable      |
        |  * Event management system;                          |    rendering styles;                                 |
        |  * Tools such as merging and exporting data in other |  * Several Python libraries available:               |
        |    formats.                                          |    :Vedo:`Vedo <>`.                                  |
        +------------------------------------------------------+------------------------------------------------------+

The **SSD** project also provides a compatible layer with :SOFA:`SOFA <>` framework:

    .. table::
        :widths: 50 50
        :class: tight-table

        +------------------------------------------------------+------------------------------------------------------+
        | ``SSD.SOFA.Storage``                                 | ``SSD.SOFA.Rendering``                               |
        |  * Same features as Core Storage package;            |  * Same features as Core Rendering package;          |
        |  * Compatible layer with :SOFA:`SOFA <>` Python      |  * Compatible layer with :SOFA:`SOFA <>` Python      |
        |    bindings.                                         |    bindings.                                         |
        |  * Callbacks to automatically record any Data field  |  * Callbacks to automatically record visual Data     |
        |    of SOFA objects.                                  |    fields of SOFA objects.                           |
        |  * Recording can be done whether the simulation is   |  * Recording can be done whether the simulation is   |
        |    running with ``runSofa`` or with a ``python``     |    running with ``runSofa`` or with a ``python``     |
        |    interpreter.                                      |    interpreter.                                      |
        |                                                      |  * Rendering is available when a simulation is       |
        |                                                      |    driven with a ``python`` interpreter.             |
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

    Install      <Presentation/install.rst>
    Definitions  <Presentation/definitions.rst>


.. toctree::
    :caption: STORAGE
    :maxdepth: 1
    :hidden:

    Database             <Core/Storage/database.rst>
    Table Relationships  <Core/Storage/relationships.rst>
    Utils                <Core/Storage/utils.rst>
    API                  <Core/Storage/api.rst>

.. toctree::
    :caption: RENDERING
    :maxdepth: 1
    :hidden:

    Factory     <Core/Rendering/factory.rst>
    Visualizer  <Core/Rendering/visualizer.rst>
    API         <Core/Rendering/api.rst>

.. toctree::
    :caption: SOFA
    :maxdepth: 1
    :hidden:

    Storage    <SOFA/storage.rst>
    Rendering  <SOFA/rendering.rst>
    API        <SOFA/api.rst>