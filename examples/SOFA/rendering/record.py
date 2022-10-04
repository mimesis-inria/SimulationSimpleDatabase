import Sofa

from SSD.SOFA.Rendering.VedoVisualizer import VedoVisualizer
from Liver import Liver

USE_GUI = True


def createScene(node):

    global USE_GUI

    # The script is launched with "runSofa"
    if USE_GUI:
        node.addObject(Liver(node, name='Controller'))

    # The script is launched with "python3" then create a Visualizer
    else:
        visualizer = VedoVisualizer(database_name='liver', remove_existing=True)
        node.addObject(Liver(node, database=visualizer.get_database(), name='Controller'))
        return visualizer


if __name__ == '__main__':

    USE_GUI = False

    # Init the scene graph and the Visualizer
    root = Sofa.Core.Node('root')
    viewer = createScene(root)
    Sofa.Simulation.init(root)
    viewer.init_visualizer()

    # Run a few steps of simulation and render them
    for _ in range(300):
        Sofa.Simulation.animate(root, root.dt.value)
