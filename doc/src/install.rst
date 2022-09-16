Install
=======

Prerequisites
-------------

**AdaptiveDB** project has the following dependencies:

.. table::
    :widths: 20 20 10 30

    +------------------------+---------------------+--------------+------------------------+
    | **Package**            | **Dependency**      | **Type**     | **Install**            |
    +========================+=====================+==============+========================+
    | :guilabel:`AdaptiveDB` | :Peewee:`Peewee <>` | **Required** | ``pip install peewee`` |
    |                        +---------------------+--------------+------------------------+
    |                        | :Numpy:`Numpy <>`   | **Required** | ``pip install numpy``  |
    +------------------------+---------------------+--------------+------------------------+


Install
-------

Install with pip
""""""""""""""""

**AdaptativeDB** is registered on :PyPi:`PyPi <>`, thus it can easily be installed using ``pip``:

.. code-block:: bash

    $ pip3 install AdaptiveDB

Then, you should be able to run:

.. code-block:: bash

    $ pip3 show AdaptiveDB

.. code-block:: python

    from AdaptiveDB import *


Install from sources
""""""""""""""""""""

Start by cloning the **AdaptiveDB** source code from its Github repository:

.. code-block:: bash

    $ git clone https://github.com/mimesis-inria/AdaptiveDB.git
    $ cd AdaptiveDB

Then, you have two options to install the project:

 * (USERS) either by using ``pip`` to install it as non-editable in the site-packages;

    .. code-block:: bash

        $ pip3 install .

 * (DEVELOPERS) either by running the ``dev.py`` script to link it as editable in the site-packages.

    .. code-block:: bash

        # Create a link to AdaptiveDB package in the site-packages
        $ python3 dev.py set
        # Remove the link to AdaptiveDB in the site-packages
        $ python3 dev.py del

Then, you should be able to run:

.. code-block:: bash

    # Only if installed with pip
    $ pip3 show AdaptiveDB

.. code-block:: python

    # In both options
    from AdaptiveDB import *
