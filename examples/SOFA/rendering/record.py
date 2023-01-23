import Sofa

from SSD.SOFA.Rendering.UserAPI import UserAPI
from Liver import Liver

USE_GUI = True


def createScene(node):

    global USE_GUI

    # The script is launched with "runSofa"
    if USE_GUI:
        node.addObject(Liver(node, name='Controller'))

    # The script is launched with "python3" then create a Visualizer
    else:
        factory = UserAPI(root=root, database_name='liver', remove_existing=True)
        node.addObject(Liver(node, factory=factory, name='Controller'))
        return factory


if __name__ == '__main__':

    USE_GUI = False

    # Init the scene graph and the Visualizer
    root = Sofa.Core.Node('root')
    api = createScene(root)
    Sofa.Simulation.init(root)
    api.launch_visualizer()

    # Run a few steps of simulation and render them
    for _ in range(30):
        Sofa.Simulation.animate(root, root.dt.value)

    api.close()
