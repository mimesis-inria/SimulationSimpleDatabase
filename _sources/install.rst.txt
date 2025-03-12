Install
=======

Prerequisites
-------------

The **SSD** project has the following dependencies:

.. table::
    :widths: 20 20 10 30

    +--------------+-----------------------+--------------+----------------------------------------------------+
    | **Package**  | **Dependency**        | **Type**     | **Install**                                        |
    +==============+=======================+==============+====================================================+
    | ``SSD.core`` | :Peewee:`Peewee <>`   | **Required** | :guilabel:`pip install peewee`                     |
    |              +-----------------------+--------------+----------------------------------------------------+
    |              | :Numpy:`Numpy <>`     | **Required** | :guilabel:`pip install numpy`                      |
    +--------------+-----------------------+--------------+----------------------------------------------------+
    | ``SSD.sofa`` | :SP3:`SofaPython3 <>` | Optional     | :SP3:`Follow instructions <menu/Compilation.html>` |
    +--------------+-----------------------+--------------+----------------------------------------------------+

.. warning::
    The :SOFA:`SOFA <>` Python bindings are not required to use the ``SSD.core`` package, but they are obviously
    required to use the ``SSD.sofa`` package. This will be ignored during the installation process if :SOFA:`SOFA <>`
    Python bindings are not found by the interpreter.


Install
-------

Install with *pip*
""""""""""""""""""

**SSD** can be easily installed with :guilabel:`pip` for users:

.. code-block:: bash

    pip install git+https://github.com/mimesis-inria/SimulationSimpleDatabase.git

Then, you should be able to run:

.. code-block:: python

    import SSD

Install from sources
""""""""""""""""""""

**SSD** can also be installed from sources for developers:

.. code-block:: bash

    git clone https://github.com/mimesis-inria/SimulationSimpleDatabase.git SSD
    cd SSD
    pip install -e .

You should be able to run:

.. code-block:: python

    import SSD

