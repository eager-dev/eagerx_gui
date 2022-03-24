from eagerx.core.graph import Graph
from eagerx_gui.gui import Gui
from pyqtgraph.Qt import QtGui


def test_gui():
    app = QtGui.QApplication([])
    graph = Graph.create()
    gui = Gui(graph._state)
