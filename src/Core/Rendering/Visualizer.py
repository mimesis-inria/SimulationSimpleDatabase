from typing import Optional, Tuple
from threading import Thread
from subprocess import run
from sys import executable, argv
from inspect import stack, getmodule

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering.backend.BaseVisualizer import BaseVisualizer


class Visualizer:

    def __init__(self,
                 backend: str = 'vedo',
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False,
                 fps: int = 20,
                 nb_clients: int = 1):
        """
        The Visualizer is used to launch either the VedoVisualizer either the Open3dVisualizer.
        It is recommended to launch the visualizer with UserAPI.launch_visualizer() method.

        :param backend: The name of the Visualizer to use (either 'vedo' or 'open3d').
        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        :param nb_clients: Number of Factories to connect to.
        """

        # Check backend
        if backend.lower() not in (available := ['vedo', 'open3d']):
            raise ValueError(f"The backend '{backend}' is not available. Must be in {available}")

        # Create the Visualizer
        self.__visualizer: BaseVisualizer
        if backend.lower() == 'vedo':
            from SSD.Core.Rendering.backend.Vedo.VedoVisualizer import VedoVisualizer
            self.__visualizer = VedoVisualizer(database=database,
                                               database_dir=database_dir,
                                               database_name=database_name,
                                               remove_existing=remove_existing,
                                               offscreen=offscreen,
                                               fps=fps)
        else:
            from SSD.Core.Rendering.backend.Open3d.Open3dVisualizer import Open3dVisualizer
            self.__visualizer = Open3dVisualizer(database=database,
                                                 database_dir=database_dir,
                                                 database_name=database_name,
                                                 remove_existing=remove_existing,
                                                 offscreen=offscreen,
                                                 fps=fps)

        self.__start_visualizer(nb_clients=nb_clients)

    def get_database(self) -> Database:
        """
        Get the Database instance.
        """

        return self.__visualizer.database

    def get_database_path(self) -> Tuple[str]:
        """
        Get the path to the Database.
        """

        return self.__visualizer.database_path

    def __start_visualizer(self,
                           nb_clients: int) -> None:
        """
        Start the Visualizer: create all Actors and render them.

        :param nb_clients: Number of Factories to connect to.
        """

        # Check that the Visualizer was launched with Visualizer.launch() method
        if getmodule(stack()[-1][0]).__file__ != __file__:
            quit(print("Warning: The Visualizer should be launched with the 'launch' method. "
                       "Check usage in documentation."))
        self.__visualizer.start_visualizer(nb_clients)

    @staticmethod
    def launch(backend: str = 'vedo',
               database_dir: str = '',
               database_name: str = '',
               offscreen: bool = False,
               fps: int = 20,
               nb_clients: int = 1) -> None:
        """
        Launch the Open3dVisualizer in a new process to keep it interactive.

        :param backend: The name of the Visualizer to use (either 'vedo' or 'open3d').
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        :param nb_clients: Number of Factories to connect to.
        """

        # Launch a new process
        t = Thread(target=Visualizer.__launch,
                   args=(backend, database_dir, database_name, offscreen, fps, nb_clients))
        t.daemon = True
        t.start()

    @staticmethod
    def __launch(backend: str,
                 database_dir: str,
                 database_name: str,
                 offscreen: bool,
                 fps: int,
                 nb_clients: int) -> None:

        run([executable, __file__,
             backend, f'{database_dir}%%{database_name}', str(offscreen), str(fps), str(nb_clients)])


def __launch_subprocess():
    # Load the existing Database
    db_path = argv[2].split('%%')
    db = Database(database_dir=db_path[0],
                  database_name=db_path[1]).load()
    # Create the Visualizer
    Visualizer(backend=argv[1],
               database=db,
               offscreen=argv[3] == 'True',
               fps=int(argv[4]),
               nb_clients=int(argv[5]))


if __name__ == '__main__':
    # This script is run in a dedicated subprocess with the call to Visualizer.launch()
    __launch_subprocess()
