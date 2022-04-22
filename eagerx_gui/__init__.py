__version__ = "0.2.1"

import os

os.environ["PYQTGRAPH_QT_LIB"] = "PyQt6"

import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from eagerx_gui.gui import Gui, EngineGui
import sys


def launch_gui(state):
    app = QtWidgets.QApplication(sys.argv)

    ## Create main window with grid layout
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("EAGERx Graph")
    cw = QtWidgets.QWidget()
    win.setCentralWidget(cw)
    layout = QtWidgets.QGridLayout()
    cw.setLayout(layout)

    rx_gui = Gui(state)
    w = rx_gui.widget()

    # Add flowchart control panel to the main window
    layout.addWidget(w, 0, 0, 2, 1)

    win.show()

    app.exec()
    new_state = rx_gui.state()
    app.quit()
    return new_state


def launch_engine_gui(state):
    app = QtWidgets.QApplication(sys.argv)

    ## Create main window with grid layout
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("EAGERx EngineGraph")
    cw = QtWidgets.QWidget()
    win.setCentralWidget(cw)
    layout = QtWidgets.QGridLayout()
    cw.setLayout(layout)

    rx_gui = EngineGui(state)
    w = rx_gui.widget()

    # Add flowchart control panel to the main window
    layout.addWidget(w, 0, 0, 2, 1)

    win.show()

    app.exec()
    new_state = rx_gui.state()
    app.quit()
    return new_state
