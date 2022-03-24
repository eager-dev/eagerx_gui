from eagerx.core.graph import Graph
from eagerx_gui.gui import Gui


def test_gui():
    graph = Graph.create()
    gui = Gui(graph._state)
