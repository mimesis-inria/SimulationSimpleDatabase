# SimulationSimpleDatabase (SSD)

![logo](docs/src/_static/images/logo.svg)

The **SSD** project provides Python3 tools to easily develop a **storage** management system for **any synthetic data**
from **numerical simulations** with a minimal lines of code.

The project is mainly using the [Peewee](http://docs.peewee-orm.com/en/latest/) Python3 library and was mostly designed 
to fit the [**DeepPhysX**](https://github.com/mimesis-inria/DeepPhysX) and [**SOFA**](https://www.sofa-framework.org/) 
frameworks.

Discover more about the project on the dedicated 
[**Documentation**](https://simulationsimpledatabase.readthedocs.io/en/latest/).


## Gallery

|      **examples/SOFA/rendering-offscreen/replay.py**      |
|:---------------------------------------------------------:|
| ![caduceus](docs/src/_static/images/gallery_caduceus.png) |

|        **examples/SOFA/rendering/replay.py**        |
|:---------------------------------------------------:|
| ![liver](docs/src/_static/images/gallery_liver.png) |


## Features

The **SSD** project provides the following `Core` features:
  * Automatic management of Database file for any data;
  * Creation of highly customizable Tables in the Database;
  * Easy writing and reading user interface; 
  * Event management system;
  * Tools such as merging and exporting data in other formats.

The **SSD** project also provides a `SOFA` compatible package with additional features:
  * Callbacks to automatically record any Data field of SOFA objects;
  * Recording can be done whether the simulation is running with *runSofa* or with a *python* interpreter.


## Install

``` bash
# Option 1 (USERS): install with pip
$ pip install git+https://github.com/mimesis-inria/SimulationSimpleDatabase.git

# Option 2 (DEVS): install as editable
$ git clone https://github.com/mimesis-inria/SimulationSimpleDatabase.git
$ cd SimRender
$ pip install -e .
```
