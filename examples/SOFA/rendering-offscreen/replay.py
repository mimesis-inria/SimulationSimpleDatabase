from os.path import exists

from SSD.SOFA.Rendering.ReplayVisualizer import ReplayVisualizer


# Check Database existence
if not exists('caduceus.db'):
    raise FileNotFoundError("You must create the Database using `python3 record.py` before to replay it.")

# Launch Visualizer
visualizer = ReplayVisualizer(database_name='caduceus')
visualizer.init_visualizer()
