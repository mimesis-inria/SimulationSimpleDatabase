from SSD.Core.Storage.Database import Database


class BaseReplay:

    def __init__(self,
                 database: Database,
                 fps: int = 20):

        pass

    def launch(self) -> None:

        raise NotImplementedError
