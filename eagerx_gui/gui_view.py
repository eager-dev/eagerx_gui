"""
 Adapted from https://github.com/pyqtgraph/pyqtgraph/blob/master/pyqtgraph/flowchart/FlowchartGraphicsView.py
"""
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph.widgets.GraphicsView import GraphicsView
from pyqtgraph.graphicsItems.ViewBox import ViewBox


class RxView(GraphicsView):

    sigHoverOver = QtCore.Signal(object)
    sigClicked = QtCore.Signal(object)

    def __init__(self, widget, *args):
        GraphicsView.__init__(self, *args, useOpenGL=False)
        self.setBackground((255, 255, 255))
        self._vb = RxViewBox(widget, lockAspect=True, invertY=True)
        self.setCentralItem(self._vb)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

    def viewBox(self):
        return self._vb


class RxViewBox(ViewBox):
    def __init__(self, widget, *args, **kwargs):
        ViewBox.__init__(self, *args, **kwargs)
        self.widget = widget

    def getMenu(self, ev):
        ## called by ViewBox to create a new context menu
        self._fc_menu = QtWidgets.QMenu()
        self._subMenus = self.getContextMenus(ev)
        for menu in self._subMenus:
            self._fc_menu.addMenu(menu)
        return self._fc_menu

    def getContextMenus(self, ev):
        ## called by scene to add menus on to someone else's context menu
        return [ViewBox.getMenu(self, ev)]
