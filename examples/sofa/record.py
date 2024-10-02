import Sofa

from Caduceus import Caduceus

USE_GUI = True


def createScene(node):

    global USE_GUI

    # The script is launched with "runSofa"
    if USE_GUI:
        node.addObject(Caduceus(node, name='Controller'))

    # The script is launched with "python3" then create a Database
    else:
        node.addObject(Caduceus(node, database=True, name='Controller'))


if __name__ == '__main__':

    USE_GUI = False

    # Init the scene graph
    root = Sofa.Core.Node('root')
    createScene(root)
    Sofa.Simulation.init(root)

    # Run a few steps of simulation and render them
    for _ in range(100):
        Sofa.Simulation.animate(root, root.dt.value)
