from os.path import exists

from SSD.SOFA.Rendering.Replay import Replay


# Check Database existence
if not exists('liver.db'):
    raise FileNotFoundError("You must create the Database using `python3 record.py` before to replay it.")

# Launch Visualizer
Replay(database_name='liver').launch()
