from eagerx.core.graph import Graph
from eagerx_gui.gui import Gui
from pyqtgraph.Qt import QtGui


def test_gui():
    graph = Graph.create()
    app = QtGui.QApplication([])
    gui = Gui(graph._state)
