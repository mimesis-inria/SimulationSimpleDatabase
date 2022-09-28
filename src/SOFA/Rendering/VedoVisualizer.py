from typing import Optional

from SSD.Core.Rendering.VedoVisualizer import VedoVisualizer as _VedoVisualizer
from SSD.SOFA.Storage.Database import Database


class VedoVisualizer(_VedoVisualizer):

    def __init__(self,
                 database: Optional[Database] = None,
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False):
        """
        Manage the creation, update and rendering of Vedo Actors.

        :param database: Database to connect to.
        :param database_name: Name of the Database (used if 'database' is not defined).
        :param remove_existing: If True, overwrite a Database with the same path.
        :param offscreen: If True, visual data will be saved but not rendered.
        """

        _VedoVisualizer.__init__(self,
                                 database=database,
                                 database_name=database_name,
                                 remove_existing=remove_existing,
                                 offscreen=offscreen)
