from os.path import exists
from os import system

from SSD.SOFA.Rendering import Replay


# Check Database existence
if not exists('caduceus.db'):
    system('python3 record.py')

# Launch Visualizer
Replay(database_name='caduceus', fps=50).launch()
