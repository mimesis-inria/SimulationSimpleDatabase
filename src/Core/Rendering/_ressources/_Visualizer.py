from typing import Dict, Optional, Any, Tuple, Union

from SSD.Core.Storage.Database import Database


class _Visualizer:

    def __init__(self,
                 database: Optional[Database] = None,
                 database_dir: str = '',
                 database_name: Optional[str] = None,
                 remove_existing: bool = False,
                 offscreen: bool = False,
                 fps: int = 20):

        if database is None and database_name is None:
            raise ValueError("Both 'database' and 'database_name' are not defined.")

    def get_database(self) -> Database:
        raise NotImplementedError

    def get_database_path(self) -> Tuple[str]:
        raise NotImplementedError

    def get_actor(self, actor_name: str) -> Any:
        raise NotImplementedError

    def init_visualizer(self, nb_clients: int) -> None:
        raise NotImplementedError
