from SSD.Core.Rendering.ReplayVisualizer import ReplayVisualizer as _ReplayVisualizer


class ReplayVisualizer(_ReplayVisualizer):

    def __init__(self,
                 database_name: str,
                 database_dir: str = ''):
        """
        Replay a simulation from saved visual data.

        :param database_name: Name of the Database.
        :param database_dir: Directory of the Database.
        """

        _ReplayVisualizer.__init__(self,
                                   database_name=database_name,
                                   database_dir=database_dir)
