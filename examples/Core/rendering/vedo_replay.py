from os.path import exists

from SSD.Core.Rendering.Replay import Replay

# Check Database existence
if not exists('vedo_example.db'):
    raise FileNotFoundError("You must create the Database using `python3 vedo_visualization.py` before to replay it.")

# Launch Vedo replay
Replay(database_name='vedo_example',
       backend='vedo').launch()

# Launch Open3d replay
Replay(database_name='vedo_example',
       backend='open3d').launch()
