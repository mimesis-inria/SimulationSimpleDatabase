from os.path import exists
from os import system
from sys import argv

from SSD.Core.Rendering import Replay

# Check Database existence
if not exists('my_databases/visualization.db'):
    system('python3 visualization.py')

# Launch replay
Replay(database_dir='my_databases',
       database_name='visualization',
       backend='vedo' if len(argv) == 1 else argv[1]).launch()
