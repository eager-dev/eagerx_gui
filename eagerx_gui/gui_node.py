"""
 Adapted from https://github.com/pyqtgraph/pyqtgraph/blob/master/pyqtgraph/flowchart/Node.py
"""

import numpy as np

from eagerx_gui import configuration
from eagerx_gui.utils import get_yaml_type
from eagerx_gui.gui_terminal import GuiTerminal
from eagerx_gui.pyqtgraph_utils import ParamWindow

from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph import functions as fn
from collections import OrderedDict

translate = QtCore.QCoreApplication.translate


class RxGuiNode(QtCore.QObject):
    sigTerminalAdded = QtCore.Signal(object, object)  # self, term

    def __init__(self, name, gui):
        QtCore.QObject.__init__(self)
        self.name = name
        self._graphics_item = None
        self.terminals = OrderedDict()
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.gui = gui
        self.spec = self.gui.graph.get_spec(name).config

        if self.gui.is_engine:
            self.is_object = False
            self.node_type = "engine_node"
        elif name in ["env/actions", "env/observations", "env/render"]:
            # todo: check if sensors actuators should be added here
            self.node_type = name.split("/")[-1]
            self.is_object = False
        else:
            self.node_type = get_yaml_type(self.gui.graph.get_spec(name).params)
        self.allow_remove = True
        self.allow_add_terminal = False
        self.__initialize_terminals()

    def __next_terminal_name(self, name):
        """Return an unused terminal name"""
        name2 = name
        i = 1
        while name2 in self.terminals:
            name2 = "%s_%d" % (name, i)
            i += 1
        return name2

    def __initialize_terminals(self):
        for terminal_type in set.union(configuration.TERMS_IN, configuration.TERMS_OUT):
            if self.node_type == "render" and terminal_type == "outputs":
                continue
            if terminal_type in self.params():
                for terminal in self.params()[terminal_type]:
                    # Filter out terminals step, and set for actions, observations and render nodes
                    if (
                        (self.node_type == "actions" and (terminal_type == "inputs" or terminal == "set"))
                        or (self.node_type in ["observations", "render"] and terminal_type == "outputs")
                        or (self.node_type == "observations" and terminal == "actions_set")
                    ):
                        continue
                    name = terminal_type + "/" + terminal
                    self.add_terminal(name=name)
                    if self.node_type == "reset_node" and terminal_type == "outputs":
                        name = "feedthroughs/" + terminal
                        self.add_terminal(name=name)

    def params(self):
        return self.spec.to_dict()

    def get_view(self):
        return self.gui.get_view(self.name, depth=["config"])

    def add_terminal(self, name):
        """Add a new terminal to this Node with the given name.

        Causes sigTerminalAdded to be emitted."""
        name = self.__next_terminal_name(name)

        term = GuiTerminal(self, name)
        self.terminals[name] = term

        if term.is_input:
            self.inputs[name] = term
        else:
            self.outputs[name] = term

        self.graphics_item().update_terminals()
        self.sigTerminalAdded.emit(self, term)
        return term

    def graphics_item(self):
        """Return the GraphicsItem for this node."""
        if self._graphics_item is None:
            self._graphics_item = NodeGraphicsItem(self)
        return self._graphics_item

    def dependent_nodes(self):
        """Return the list of nodes which provide direct input to this node"""
        nodes = set()
        for t in self.inputs.values():
            nodes |= set([i.node for i in t.input_terminals()])
        return nodes

    def __repr__(self):
        return "<Node %s @%x>" % (self.name, id(self))

    def connected(self, local_term, remote_term):
        """Called whenever one of this node's terminals is connected elsewhere."""
        pass

    def recolor(self):
        self.graphics_item().setPen(QtGui.QPen(QtGui.QColor(150, 0, 0), 3))

    def load_state(self, state):
        pos = state["gui_state"].get("pos", (0, 0))
        self.graphics_item().setPos(*pos)


class TextItem(QtWidgets.QGraphicsTextItem):
    def __init__(self, text, parent, on_update):
        super().__init__(text, parent)
        self.on_update = on_update

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        if self.on_update is not None:
            self.on_update()

    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key.Key_Enter or ev.key() == QtCore.Qt.Key.Key_Return:
            if self.on_update is not None:
                self.on_update()
                return
        super().keyPressEvent(ev)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)  # focus text label


class NodeGraphicsItem(GraphicsObject):
    def __init__(self, node):
        GraphicsObject.__init__(self)
        self.node = node
        self._node_type = node.node_type
        flags = (
            self.GraphicsItemFlag.ItemIsMovable
            | self.GraphicsItemFlag.ItemIsSelectable
            | self.GraphicsItemFlag.ItemIsFocusable
            | self.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.set_color()
        self.setFlags(flags)
        self.bounds = QtCore.QRectF(0, 0, 125, 125)
        self.nameItem = TextItem(self.node.name, self, self.label_changed)
        self.nameItem.setDefaultTextColor(QtGui.QColor(50, 50, 50))
        self.nameItem.moveBy(self.bounds.width() / 2.0 - self.nameItem.boundingRect().width() / 2.0, 0)
        self.update_terminals()

        self.nameItem.focusOutEvent = self.label_focus_out
        self.nameItem.keyPressEvent = self.label_key_press

        self.menu = None
        self.buildMenu()
        self.initial_z_value = self.zValue()
        self.label_changed()

    def set_color(self):
        if "color" in self.node.params() and self.node.params()["color"] in configuration.GUI_COLORS:
            brush_color = np.array(configuration.GUI_COLORS[self.node.params()["color"]])
        else:
            brush_color = np.array([200, 200, 200])

        self.brush = fn.mkBrush(*brush_color, 50)
        self.hoverBrush = fn.mkBrush(*brush_color, 100)
        self.selectBrush = fn.mkBrush(*brush_color, 100)
        self.pen = fn.mkPen(0, 0, 0, 200, width=2)
        self.selectPen = fn.mkPen(0, 0, 0, 200, width=4)
        self.hovered = False
        self.update()

    def label_focus_out(self, ev):
        QtWidgets.QGraphicsTextItem.focusOutEvent(self.nameItem, ev)
        self.label_changed()

    def label_key_press(self, ev):
        if ev.key() == QtCore.Qt.Key.Key_Enter or ev.key() == QtCore.Qt.Key.Key_Return:
            self.label_changed()
        else:
            QtWidgets.QGraphicsTextItem.keyPressEvent(self.nameItem, ev)

    def label_changed(self):
        new_name = str(self.nameItem.toPlainText())
        if self.node.gui is not None and new_name in self.node.gui.nodes.keys():
            self.nameItem.setPlainText(self.node.name)
            return
        if new_name != self.node.name:
            self.node.rename(new_name)
        self.update_terminals()

    def setPen(self, *args, **kwargs):
        self.pen = fn.mkPen(*args, **kwargs)
        self.update()

    def setBrush(self, brush):
        self.brush = brush
        self.update()

    def update_terminals(self):
        # re-center the label
        if self.nameItem.boundingRect().width() > self.bounds.width() - 5.0:
            self.bounds = QtCore.QRectF(0, 0, self.nameItem.boundingRect().width() + 5.0, self.bounds.height())
        bounds = self.boundingRect()
        self.nameItem.setPos(bounds.width() / 2.0 - self.nameItem.boundingRect().width() / 2.0, 0)

        # Update bounds
        bounds = self.bounds
        self.terminals = {}
        inp = self.node.inputs
        y = self.nameItem.boundingRect().height() + 5
        max_width_inp = 0.0
        for i in sorted(inp.keys()):
            t = inp[i]
            item = t.graphics_item()
            item.setParentItem(self)
            br = self.bounds
            item.set_anchor(0, y)
            self.terminals[i] = (t, item)
            y += item.boundingRect().height() + 2
            if item.boundingRect().width() > max_width_inp:
                max_width_inp = item.boundingRect().width()
        y_inp = y

        out = self.node.outputs
        dy = bounds.height() / (len(out) + 1)
        y = self.nameItem.boundingRect().height() + 5
        max_width_out = 0.0
        for i in sorted(out.keys()):
            t = out[i]
            item = t.graphics_item()
            item.setParentItem(self)
            item.setZValue(self.initial_z_value)
            br = self.bounds
            item.set_anchor(bounds.width(), y)
            self.terminals[i] = (t, item)
            y += item.boundingRect().height() + 2
            if item.boundingRect().width() > max_width_out:
                max_width_out = item.boundingRect().width()
        y_max = max(y_inp, y)

        if y_max > bounds.height() - 5:
            self.bounds = QtCore.QRectF(0, 0, self.bounds.width(), y_max + 6.0)

        if max_width_inp + max_width_out > bounds.width() - 10:
            self.bounds = QtCore.QRectF(0, 0, max_width_inp + max_width_out + 11.0, self.bounds.height())
            self.update_terminals()
        self.update()

    def boundingRect(self):
        return self.bounds.adjusted(-5, -5, 5, 5)

    def paint(self, p, *args):
        p.setPen(self.pen)
        if self.isSelected():
            p.setPen(self.selectPen)
            p.setBrush(self.selectBrush)
            self.setZValue(200)
        else:
            p.setPen(self.pen)
            if self.hovered:
                p.setBrush(self.hoverBrush)
                self.setZValue(200)
            else:
                p.setBrush(self.brush)
                self.setZValue(self.initial_z_value)

        p.drawRect(self.bounds)

    def mousePressEvent(self, ev):
        ev.ignore()

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            sel = self.isSelected()
            self.setSelected(True)
            if not sel and self.isSelected():
                self.update()

        elif ev.button() == QtCore.Qt.MouseButton.RightButton:
            self.menu = None
            self.buildMenu()
            ev.accept()
            self.raiseContextMenu(ev)

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            # todo: find out which keys to suppress in dialog
            filter = []
            widgets_to_hide = configuration.GUI_WIDGETS["node"]["hide"]
            for key in self.node.params().keys():
                if key in widgets_to_hide["all"]:
                    filter.append(key)
                elif self._node_type in widgets_to_hide and key in widgets_to_hide[self._node_type]:
                    filter.append(key)
            param_window = ParamWindow(spec=self.node.spec, parent=self.parent(), filter=filter)
            param_window.exec()
            param_window.close()

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.LeftButton:
            ev.accept()
            self.setPos(self.pos() + self.mapToParent(ev.pos()) - self.mapToParent(ev.lastPos()))

    def hoverEvent(self, ev):
        if not ev.isExit() and ev.acceptClicks(QtCore.Qt.MouseButton.LeftButton):
            ev.acceptDrags(QtCore.Qt.MouseButton.LeftButton)
            self.hovered = True
        else:
            self.hovered = False
        self.update()

    def keyPressEvent(self, ev):
        ev.ignore()

    def itemChange(self, change, val):
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            self.node.gui.graph._state["gui_state"][self.node.name]["pos"] = [
                self.pos().x(),
                self.pos().y(),
            ]
            for k, t in self.terminals.items():
                t[1].node_moved()
        return GraphicsObject.itemChange(self, change, val)

    def getMenu(self):
        return self.menu

    def raiseContextMenu(self, ev):
        menu = self.getMenu()
        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))

    def buildMenu(self):
        self.menu = QtWidgets.QMenu()
        self.menu.setTitle("Node")
