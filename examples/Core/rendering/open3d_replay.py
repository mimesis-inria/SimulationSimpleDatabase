from os.path import exists

from SSD.Core.Rendering.Replay import Replay

# Check Database existence
if not exists('open3d_example.db'):
    raise FileNotFoundError("You must create the Database using `python3 open3d_visualization.py` before to replay it.")

# Launch Vedo replay
Replay(database_name='open3d_example',
       backend='open3d').launch()

# Launch Open3d replay
Replay(database_name='open3d_example',
       backend='vedo').launch()
