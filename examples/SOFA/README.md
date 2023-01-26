# Examples - SSD.SOFA

This repository contains a few examples that give a great overviews of the **storage** and **rendering** features.

Each repository contains the following scripts:

 * ``<Simulation_name>.py``: a SOFA Controller that describes the scene graph and the Data to store / render.
 * ``record.py``: this script can either be launched with ``runSofa record.py`` to simply run the scene in the SOFA GUI, 
                  either with ``python3 record.py`` to trigger the recording session.
 * ``replay.py``: (rendering only) read the stored visual data and render them in the Visualizer.
