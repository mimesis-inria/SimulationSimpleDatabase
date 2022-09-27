import Sofa
import os

from Caduceus import Caduceus


def createScene(node):

    node.addObject(Caduceus(node, name='Controller'))


if __name__ == '__main__':

    root = Sofa.Core.Node('root')
    createScene(root)
    Sofa.Simulation.init(root)

    for _ in range(300):
        Sofa.Simulation.animate(root, root.dt.value)

    for file in os.listdir(os.getcwd()):
        if '.ini' in file or '.log' in file:
            os.remove(file)
