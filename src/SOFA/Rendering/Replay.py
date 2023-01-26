from SSD.Core.Rendering.Replay import Replay as _Replay


class Replay(_Replay):

    def __init__(self,
                 database_name: str,
                 database_dir: str = '',
                 backend: str = 'vedo',
                 fps: int = 20):
        """
        Replay a simulation from saved visual data.

        :param database_name: Name of the Database.
        :param database_dir: Directory of the Database.
        :param backend: The name of the Visualizer to use (either 'vedo' or 'open3d').
        :param fps: Max frame rate.
        """

        _Replay.__init__(self,
                         database_name=database_name,
                         database_dir=database_dir,
                         backend=backend,
                         fps=fps)
