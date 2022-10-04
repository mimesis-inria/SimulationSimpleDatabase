Install
=======

Prerequisites
-------------

The **SSD** project has the following dependencies:

.. table::
    :widths: 20 20 10 30

    +------------------------+-----------------------+--------------+----------------------------------------------------+
    | **Package**            | **Dependency**        | **Type**     | **Install**                                        |
    +========================+=======================+==============+====================================================+
    | ``SSD.Core.Storage``   | :Peewee:`Peewee <>`   | **Required** | :guilabel:`pip install peewee`                     |
    |                        +-----------------------+--------------+----------------------------------------------------+
    |                        | :Numpy:`Numpy <>`     | **Required** | :guilabel:`pip install numpy`                      |
    +------------------------+-----------------------+--------------+----------------------------------------------------+
    | ``SSD.Core.Rendering`` | :Vedo:`Vedo <>`       | **Required** | :guilabel:`pip install vedo`                       |
    +------------------------+-----------------------+--------------+----------------------------------------------------+
    | ``SSD.SOFA``           | :SP3:`SofaPython3 <>` | Optional     | :SP3:`Follow instructions <menu/Compilation.html>` |
    +------------------------+-----------------------+--------------+----------------------------------------------------+

.. warning::
    The :SOFA:`SOFA <>` Python bindings are not required to use the ``SSD.Core`` packages, but they are obviously
    required to use the ``SSD.SOFA.Storage`` and ``SSD.SOFA.rendering`` packages. Those two packages will be ignored
    during the installation process if :SOFA:`SOFA <>` Python bindings are not found by the interpreter.

Install
-------

Install with pip
""""""""""""""""

The **SSD** project is registered on :PyPi:`PyPi <>`, thus it can easily be installed using :guilabel:`pip`:

.. code-block:: bash

    $ pip3 install SimulationSimpleDatabase

Then, you should be able to run:

.. code-block:: bash

    $ pip3 show SSD

.. code-block:: python

    from SSD import *


Install from sources
""""""""""""""""""""

Start by cloning the **SSD** source code from its Github repository:

.. code-block:: bash

    $ git clone https://github.com/mimesis-inria/SimulationSimpleDatabase.git
    $ cd SimpleSimulationDatabase

Then, you have two options to install the project:

 * (USERS) either by using ``pip`` to install it as non-editable in the site-packages;

    .. code-block:: bash

        $ pip3 install .

 * (DEVELOPERS) either by running the ``dev.py`` script to link it as editable in the site-packages.

    .. code-block:: bash

        # Create a link to SSD packages in the site-packages
        $ python3 dev.py set
        # Remove the link to SSD packages in the site-packages
        $ python3 dev.py del

Then, you should be able to run:

.. code-block:: bash

    # Only if installed with pip
    $ pip3 show SSD

.. code-block:: python

    # In both options
    from SSD import *
