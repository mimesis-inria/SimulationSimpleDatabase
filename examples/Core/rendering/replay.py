from os.path import exists
from sys import argv

from SSD.Core.Rendering.Replay import Replay

# Check Database existence
if not exists('visualization.db'):
    raise FileNotFoundError("You must create the Database using `python3 visualization.py` before to replay it.")

# Launch replay
Replay(database_name='visualization',
       backend='vedo' if len(argv) == 1 else argv[1]).launch()
