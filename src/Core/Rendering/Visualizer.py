from typing import Dict, Optional, Any, Tuple, Union
from threading import Thread
from subprocess import run
from sys import executable, argv
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from inspect import stack, getmodule

from SSD.Core.Storage.Database import Database
from SSD.Core.Rendering._ressources._Visualizer import _Visualizer
from SSD.Core.Rendering._ressources.VedoVisualizer import VedoVisualizer, VedoActor
from SSD.Core.Rendering._ressources.Open3dVisualizer import Open3dVisualizer, Open3dActor


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
        Manage the creation, update and rendering of visual objects.

        :param backend: The name of the Visualizer to use (either 'vedo' or 'open3d').
        :param database: Database to connect to.
        :param database_dir: Directory which contains the Database file (used if 'database' is not defined).
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        """

        # Check backend
        if backend.lower() not in (available := {'vedo': VedoVisualizer, 'open3d': Open3dVisualizer}):
            raise ValueError(f"The backend '{backend}' is not available. Must be in {available}")

        self.__visualizer: _Visualizer = available[backend.lower()](database=database,
                                                                    database_dir=database_dir,
                                                                    database_name=database_name,
                                                                    remove_existing=remove_existing,
                                                                    offscreen=offscreen,
                                                                    fps=fps)
        self.init_visualizer(nb_clients)

    @staticmethod
    def launch(backend: str = 'vedo',
               database_dir: str = '',
               database_name: str = '',
               offscreen: bool = False,
               fps: int = 20) -> None:
        """
        Launch the Open3dVisualizer in a new process to keep it interactive.

        :param database_path: Path to the Database to connect to.
        :param offscreen: If True, visual data will be saved but not rendered.
        :param fps: Max frame rate.
        """

        # Launch a new process
        Thread(target=Visualizer.__launch, args=(backend, database_dir, database_name, offscreen, fps,)).start()

        # # Connect to the Factory, wait for the Visualizer to be ready
        # sock = socket(AF_INET, SOCK_STREAM)
        # sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # sock.connect(('localhost', 20000))
        # sock.send(b'L')
        # sock.recv(1)
        # sock.close()

    @staticmethod
    def __launch(backend: str,
                 database_dir: str,
                 database_name: str,
                 offscreen: bool,
                 fps: int) -> None:
        run([executable, __file__, backend, f'{database_dir}%%{database_name}', str(offscreen), str(fps)])

    def get_database(self) -> Database:
        """
        Get the Database instance.
        """

        return self.__visualizer.get_database()

    def get_database_path(self) -> Tuple[str]:
        """
        Get the path to the Database.
        """

        return self.__visualizer.get_database_path()

    def init_visualizer(self, nb_clients):
        """
        Initialize the Visualizer: create all Actors and render them in a Plotter.
        """

        if getmodule(stack()[-1][0]).__file__ != __file__:
            quit(print("Warning: The Open3dVisualizer should be launched with the 'launch' method."
                       "Check usage in documentation."))

        self.__visualizer.init_visualizer(nb_clients)


def launch_subprocess():

    db_path = argv[2].split('%%')
    db = Database(database_dir=db_path[0],
                  database_name=db_path[1]).load()
    Visualizer(backend=argv[1],
               database=db,
               offscreen=argv[3] == 'True',
               fps=int(argv[4]))


if __name__ == '__main__':
    launch_subprocess()
