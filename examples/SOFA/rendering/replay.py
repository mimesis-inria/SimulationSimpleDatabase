from os.path import exists

from SSD.Core.Rendering.ReplayVisualizer import ReplayVisualizer


# Check Database existence
if not exists('liver.db'):
    raise FileNotFoundError("You must create the Database using `python3 record.py` before to replay it.")

# Launch Visualizer
visualizer = ReplayVisualizer(database_name='liver',
                              mode='auto')
visualizer.init_visualizer()
