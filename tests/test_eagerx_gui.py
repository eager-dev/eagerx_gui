from eagerx.core.graph import Graph
from eagerx_gui.gui import Gui
from pyqtgraph.Qt import QtWidgets


def test_gui():
    graph = Graph.create()
    app = QtWidgets.QApplication([])
    gui = Gui(graph._state)
