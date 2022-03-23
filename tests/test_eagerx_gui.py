from eagerx.core.graph import Graph
from eagerx_gui import create_gui

import pytest

def test_gui():
    graph = Graph.create()
    create_gui(graph._state)
