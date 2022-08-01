"""
 Adapted from https://github.com/pyqtgraph/pyqtgraph/blob/master/pyqtgraph/flowchart/Terminal.py
"""

from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph import functions as fn
from pyqtgraph.Point import Point

from eagerx_gui import configuration
from eagerx_gui.pyqtgraph_utils import ParamWindow


class GuiTerminal(object):
    def __init__(self, node, name, pos=None):
        self.node = node
        self.name = name
        self.pos = pos
        self.optional = False
        self.connections = {}
        self.node_type = node.node_type

        name_split = name.split("/")
        self.terminal_type = name_split[0]
        self.terminal_name = name_split[-1]

        assert self.terminal_type in set.union(configuration.TERMS_IN, configuration.TERMS_OUT), (
            f"Invalid terminal type: {self.terminal_type}, "
            f"should be one of {set.union(configuration.TERMS_IN, configuration.TERMS_OUT)}"
        )

        self.is_input = self.terminal_type in configuration.TERMS_IN
        self.is_state = self.terminal_type in ["targets", "states"]
        self.is_feedthrough = self.terminal_type == "feedthroughs"
        self.is_removable = False
        self.is_renamable = False
        self.is_connectable = False

        # todo: Check if we want to show different parameters if feedthrough (e.g. of the corresponding output)
        self.spec = getattr(getattr(node.gui.graph.get_spec(node.name), self.terminal_type), self.terminal_name)

        self._graphicsItem = TerminalGraphicsItem(self, parent=self.node.graphics_item())
        self.recolor()

    def connection_view(self):
        return self.node.gui.tuple_to_view(self.connection_tuple())

    def connection_tuple(self):
        return (self.node.name, self.terminal_type, self.terminal_name)

    def connected(self, term):
        """Called whenever this terminal has been connected to another.
        (note--this function is called on both terminals)"""
        self.node.connected(self, term)

    def params(self):
        return self.spec.to_dict()

    def is_connected(self):
        return len(self.connections) > 0

    def graphics_item(self):
        return self._graphicsItem

    def connected_to(self, term):
        return term in self.connections

    def has_input(self):
        for t in self.connections:
            if not t.is_input:
                return True
        return False

    def input_terminals(self):
        """Return the terminal(s) that give input to this one."""
        return [t for t in self.connections if not t.is_input]

    def dependent_nodes(self):
        """Return the list of nodes which receive input from this terminal."""
        return set([t.node for t in self.connections if t.is_input])

    def disconnect_all(self):
        for t in list(self.connections.keys()):
            self.disconnect_from(t)

    def recolor(self, color=None, recurse=True):
        if color is None:
            if self.is_state:
                if self.is_connectable:
                    color = QtGui.QColor(255, 0, 0)
                else:
                    color = QtGui.QColor(128, 128, 128)
            elif self.is_feedthrough:
                color = QtGui.QColor(175, 238, 238)
            else:
                color = QtGui.QColor(0, 0, 255)
        self.graphics_item().setBrush(QtGui.QBrush(color))

        if recurse:
            for t in self.connections:
                t.recolor(color, recurse=False)

    def __repr__(self):
        return "<Terminal %s.%s>" % (str(self.node.name), str(self.terminal_name))

    def __hash__(self):
        return id(self)


class TextItem(QtWidgets.QGraphicsTextItem):
    def __init__(self, text, parent, on_update):
        super().__init__(text, parent)
        self.on_update = on_update

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        if self.on_update is not None:
            self.on_update()

    def keyPressEvent(self, ev):
        super().keyPressEvent(ev)


class TerminalGraphicsItem(GraphicsObject):
    def __init__(self, term, parent=None):
        self.term = term
        GraphicsObject.__init__(self, parent)
        self.brush = fn.mkBrush(0, 0, 0)
        self.box = QtWidgets.QGraphicsRectItem(0, 0, 10, 10, self)
        on_update = None
        self.label = TextItem(self.term.terminal_name, self, on_update)
        self.label.setScale(0.7)
        self.newConnection = None
        self.setFiltersChildEvents(True)  # to pick up mouse events on the rectitem
        self.setZValue(1)
        self.menu = None

    def label_focus_out(self, ev):
        QtWidgets.QGraphicsTextItem.focusOutEvent(self.label, ev)
        self.label_changed()

    def label_key_press(self, ev):
        if ev.key() == QtCore.Qt.Key.Key_Enter or ev.key() == QtCore.Qt.Key.Key_Return:
            self.label_changed()
        else:
            QtWidgets.QGraphicsTextItem.keyPressEvent(self.label, ev)

    def setBrush(self, brush):
        self.brush = brush
        self.box.setBrush(brush)

    def boundingRect(self):
        br = self.box.mapRectToParent(self.box.boundingRect())
        lr = self.label.mapRectToParent(self.label.boundingRect())
        return br | lr

    def paint(self, p, *args):
        pass

    def set_anchor(self, x, y):
        pos = QtCore.QPointF(x, y)
        self.anchorPos = pos
        br = self.box.mapRectToParent(self.box.boundingRect())
        lr = self.label.mapRectToParent(self.label.boundingRect())

        if self.term.is_input:
            self.box.setPos(pos.x(), pos.y() - br.height() / 2.0)
            self.label.setPos(pos.x() + br.width(), pos.y() - lr.height() / 2.0)
        else:
            self.box.setPos(pos.x() - br.width(), pos.y() - br.height() / 2.0)
            self.label.setPos(pos.x() - br.width() - lr.width(), pos.y() - lr.height() / 2.0)
        self.update_connections()

    def update_connections(self):
        for t, c in self.term.connections.items():
            c.update_line()

    def mousePressEvent(self, ev):
        ev.ignore()  # necessary to allow click/drag events to process correctly

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            self.label.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
        elif ev.button() == QtCore.Qt.MouseButton.RightButton:
            ev.accept()
            self.raise_context_menu(ev)

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            # todo: find out which keys to suppress in dialog
            filter = []
            terminal_type = self.term.terminal_type
            widgets_to_hide = configuration.GUI_WIDGETS["term"]["hide"]
            for key in self.term.params().keys():
                if key in widgets_to_hide["all"]:
                    filter.append(key)
                elif terminal_type in widgets_to_hide and key in widgets_to_hide[terminal_type]:
                    filter.append(key)
            param_window = ParamWindow(spec=self.term.spec, parent=self.parent(), filter=filter)
            param_window.exec()
            param_window.close()

    def raise_context_menu(self, ev):
        # only raise menu if this terminal is removable
        ev.ignore()

    def mouseDragEvent(self, ev):
        return

    def hoverEvent(self, ev):
        if not ev.isExit() and ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton):
            ev.acceptClicks(QtCore.Qt.MouseButton.LeftButton)
            # we don't use the click, but we also don't want anyone else to use it.
            ev.acceptClicks(QtCore.Qt.MouseButton.RightButton)
            self.box.setBrush(fn.mkBrush("w"))
        else:
            self.box.setBrush(self.brush)
        self.update()

    def connect_point(self):
        # return the connect position of this terminal in view coords
        return self.mapToView(self.mapFromItem(self.box, self.box.boundingRect().center()))

    def node_moved(self):
        for t, item in self.term.connections.items():
            item.update_line()


class ConnectionItem(GraphicsObject):
    def __init__(self, source, target=None):
        GraphicsObject.__init__(self)
        self.setFlags(self.GraphicsItemFlag.ItemIsSelectable | self.GraphicsItemFlag.ItemIsFocusable)
        self.source = source
        self.target = target
        self.length = 0
        self.hovered = False
        self.path = None
        self.shapePath = None
        self.connection_window = None

        if self.source.term.is_state:
            self.style = {
                "shape": "line",
                "color": (255, 0, 0, 255),
                "width": 2.0,
                "hoverColor": (150, 150, 250, 255),
                "hoverWidth": 2.0,
                "selectedColor": (200, 200, 0, 255),
                "selectedWidth": 4.0,
            }
        else:
            self.style = {
                "shape": "line",
                "color": (0, 0, 255, 255),
                "width": 2.0,
                "hoverColor": (150, 150, 250),
                "hoverWidth": 2.0,
                "selectedColor": (200, 200, 0, 255),
                "selectedWidth": 4.0,
            }
        self.source.getViewBox().addItem(self)
        self.update_line()

    def set_target(self, target):
        self.target = target
        self.update_line()

    def setStyle(self, **kwds):
        self.style.update(kwds)
        if "shape" in kwds:
            self.update_line()
        else:
            self.update()

    def update_line(self):
        start = Point(self.source.connect_point())
        if isinstance(self.target, TerminalGraphicsItem):
            stop = Point(self.target.connect_point())
            input_term = self.target.term if self.target.term.is_input else self.source.term
            node_name = input_term.node.name
            linestyle_state = input_term.node.gui.graph._state["gui_state"][node_name]["linestyle"]
            if input_term.name in linestyle_state:
                shape = linestyle_state[input_term.name]
            else:
                shape = "cubic"
                linestyle_state[input_term.name] = shape
            self.style["shape"] = shape
        elif isinstance(self.target, QtCore.QPointF):
            stop = Point(self.target)
        else:
            return
        self.prepareGeometryChange()

        self.path = self.generate_path(start, stop)
        self.shapePath = None
        self.update()
        self.setZValue(-1)

    def generate_path(self, start, stop):
        path = QtGui.QPainterPath()
        path.moveTo(start)
        if self.style["shape"] == "line":
            path.lineTo(stop)
        elif self.style["shape"] == "cubic":
            path.cubicTo(
                Point(stop.x(), start.y()),
                Point(start.x(), stop.y()),
                Point(stop.x(), stop.y()),
            )
        else:
            raise Exception('Invalid shape "%s"; options are "line" or "cubic"' % self.style["shape"])
        return path

    def keyPressEvent(self, ev):
        if not self.isSelected():
            ev.ignore()
            return

        if ev.key() == QtCore.Qt.Key.Key_Control:
            ev.accept()
            if self.style["shape"] == "line":
                shape = "cubic"
            elif self.style["shape"] == "cubic":
                shape = "line"
            if isinstance(self.target, TerminalGraphicsItem):
                # Update linestyle in gui state
                input_term = self.target.term if self.target.term.is_input else self.source.term
                node_name = input_term.node.name
                input_term.node.gui.graph._state["gui_state"][node_name]["linestyle"][input_term.name] = shape
                self.setStyle(shape=shape)
        else:
            ev.ignore()

    def mousePressEvent(self, ev):
        ev.ignore()

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            sel = self.isSelected()
            self.setSelected(True)
            self.setFocus()
            if not sel and self.isSelected():
                self.update()

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            if self.connection_window is not None:
                self.connection_window.show()

    def hoverEvent(self, ev):
        if (not ev.isExit()) and ev.acceptClicks(QtCore.Qt.MouseButton.LeftButton):
            self.hovered = True
        else:
            self.hovered = False
        self.update()

    def boundingRect(self):
        return self.shape().boundingRect()

    def viewRangeChanged(self):
        self.shapePath = None
        self.prepareGeometryChange()

    def shape(self):
        if self.shapePath is None:
            if self.path is None:
                return QtGui.QPainterPath()
            stroker = QtGui.QPainterPathStroker()
            px = self.pixelWidth()
            stroker.setWidth(px * 8)
            self.shapePath = stroker.createStroke(self.path)
        return self.shapePath

    def paint(self, p, *args):
        if self.isSelected():
            p.setPen(fn.mkPen(self.style["selectedColor"], width=self.style["selectedWidth"]))
        else:
            if self.hovered:
                p.setPen(fn.mkPen(self.style["hoverColor"], width=self.style["hoverWidth"]))
            else:
                p.setPen(fn.mkPen(self.style["color"], width=self.style["width"]))

        p.drawPath(self.path)
