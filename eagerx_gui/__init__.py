__version__ = "0.2.8"

import os

# Set PyQt backend
for lib in ["PyQt6", "PyQt5"]:
    try:
        __import__(lib)
        os.environ["PYQTGRAPH_QT_LIB"] = lib
        break
    except ImportError:
        pass

import pyqtgraph as pg
import pyqtgraph.exporters
import sys
import numpy as np
from pyqtgraph.Qt import QtWidgets, QtGui
from eagerx_gui.gui import Gui


def launch_gui(state, is_engine=False):
    app = QtWidgets.QApplication(sys.argv)

    ## Create main window with grid layout
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("EAGERx Graph")
    cw = QtWidgets.QWidget()
    win.setCentralWidget(cw)
    layout = QtWidgets.QGridLayout()
    cw.setLayout(layout)

    rx_gui = Gui(state, is_engine=is_engine)
    w = rx_gui.widget()

    # Add flowchart control panel to the main window
    layout.addWidget(w, 0, 0, 2, 1)

    win.show()

    app.exec()
    state["gui_state"] = rx_gui.graph._state["gui_state"]
    app.quit()
    return state


def render_gui(state, shape=None, is_engine=False):
    if shape is None:
        shape = [1920, 1080]

    app = QtWidgets.QApplication(sys.argv)

    ## Create main window with grid layout
    win = QtWidgets.QMainWindow()
    win.setWindowTitle("EAGERx Graph")
    cw = QtWidgets.QWidget()
    win.setCentralWidget(cw)
    layout = QtWidgets.QGridLayout()
    cw.setLayout(layout)

    rx_gui = Gui(state, is_engine=is_engine)
    w = rx_gui.widget()

    # Add flowchart control panel to the main window
    layout.addWidget(w, 0, 0, 2, 1)

    win.show()

    exporter = pg.exporters.ImageExporter(w.view.scene())
    exporter.parameters()["width"] = shape[0]
    exporter.parameters()["height"] = shape[1]

    png = exporter.export(toBytes=True)
    png.convertToFormat(QtGui.QImage.Format.Format_RGB32)

    width = png.width()
    height = png.height()

    ptr = png.bits()
    ptr.setsize(height * width * 4)
    arr = np.array(ptr).reshape(height, width, 4)  # Copies the data
    app.quit()
    return arr[..., [2, 1, 0, 3]]


def launch_engine_gui(state):
    return launch_gui(state, is_engine=True)


def render_engine_gui(state):
    return render_gui(state, is_engine=True)
