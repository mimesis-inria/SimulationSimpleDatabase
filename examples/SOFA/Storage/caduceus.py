import Sofa
import os

from Caduceus import Caduceus


def createScene(node):

    node.gravity.value = [0, -1000, 0]
    node.dt.value = 0.04
    node.addObject(Caduceus(node, name='Controller'))


if __name__ == '__main__':

    root = Sofa.Core.Node('root')
    createScene(root)
    Sofa.Simulation.init(root)

    import Sofa.Gui
    Sofa.Gui.GUIManager.Init('caduceus', 'qglviewer')
    Sofa.Gui.GUIManager.createGUI(root, __file__)
    Sofa.Gui.GUIManager.SetDimension(1080, 1080)
    Sofa.Gui.GUIManager.MainLoop(root)
    Sofa.Gui.GUIManager.closeGUI()

    for file in os.listdir(os.getcwd()):
        if '.ini' in file or '.log' in file:
            os.remove(file)
