from typing import Optional

from SSD.SOFA.Storage.database import Database
from SSD.Core.Rendering.visualizer import Visualizer as CoreVisualizer


class Visualizer(CoreVisualizer):

    def __init__(self,
                 backend: str = 'vedo',
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
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
        :param fps: Max frame rate.
        """

        CoreVisualizer.__init__(self,
                                backend=backend,
                                database=database,
                                database_dir=database_dir,
                                database_name=database_name,
                                remove_existing=remove_existing,
                                fps=fps,
                                nb_clients=nb_clients)
