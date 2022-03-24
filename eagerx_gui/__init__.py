__version__ = "0.1.4"

import sys
from pyqtgraph.Qt import QtGui, QtCore
from eagerx_gui.gui import Gui


def create_gui(state):
    # Create main window with grid layout
    win = QtGui.QMainWindow()

    cw = QtGui.QWidget()

    layout = QtGui.QGridLayout()
    cw.setLayout(layout)

    win.setCentralWidget(cw)

    rx_gui = Gui(state)
    w = rx_gui.widget()

    # Add flowchart control panel to the main window
    layout.addWidget(w, 0, 0, 2, 1)
    return win, rx_gui


def launch_gui(state):
    app = QtGui.QApplication([])
    win, rx_gui = create_gui(state)
    win.setWindowTitle("EAGERx Graph Creator")

    win.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtGui.QApplication.instance().exec_()
    new_state = rx_gui.state()
    return new_state
