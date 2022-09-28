from os.path import exists

from SSD.SOFA.Rendering.ReplayVisualizer import ReplayVisualizer


# Check Database existence
if not exists('liver.db'):
    raise FileNotFoundError("You must create the Database using `python3 record.py` before to replay it.")

# Launch Visualizer
visualizer = ReplayVisualizer(database_name='liver')
visualizer.init_visualizer()
