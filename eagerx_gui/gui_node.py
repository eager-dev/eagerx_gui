"""
 Adapted from https://github.com/pyqtgraph/pyqtgraph/blob/master/pyqtgraph/flowchart/Node.py
"""

import numpy as np
from functools import partial

from eagerx_gui import configuration
from eagerx_gui.utils import get_yaml_type
from eagerx_gui.gui_terminal import GuiTerminal
from eagerx_gui.pyqtgraph_utils import exception_handler, ParamWindow

from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph import functions as fn
from collections import OrderedDict

translate = QtCore.QCoreApplication.translate


class RxEngineGuiNode(QtCore.QObject):
    sigClosed = QtCore.Signal(object)
    sigRenamed = QtCore.Signal(object, object)
    sigTerminalRenamed = QtCore.Signal(object, object)  # term, oldName
    sigTerminalAdded = QtCore.Signal(object, object)  # self, term
    sigTerminalRemoved = QtCore.Signal(object, object)  # self, term

    def __init__(self, name, graph):
        QtCore.QObject.__init__(self)
        self.name = name
        self._graphics_item = None
        self.terminals = OrderedDict()
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.graph = graph
        self.exception = None

        self.allow_add_terminal = False
        self.allow_remove = False
        self.is_object = False

        self.node_type = "engine_node"
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
                    if self.node_type in ["actions", "observations"]:
                        if terminal in self.default_params()[terminal_type]:
                            continue
                    name = terminal_type + "/" + terminal
                    self.add_terminal(name=name)
                    if self.node_type == "reset_node" and terminal_type == "outputs":
                        name = "feedthroughs/" + terminal
                        self.add_terminal(name=name)

    def params(self):
        return self._get_params(graph_backup=self.graph)

    @exception_handler
    def _get_params(self):
        assert self.name in self.graph._state["nodes"], f" No entity with name '{self.name}' in graph."
        return self.graph._state["nodes"][self.name]["config"]

    def default_params(self):
        return self.graph._state["backup"][self.name]

    def set_param(self, parameter, value):
        self._set_param(parameter, value, graph_backup=self.graph)

    def get_view(self):
        return self.graph.get_view(self.name, depth=["config"])

    @exception_handler
    def _set_param(self, parameter, value):
        self.graph.set(value, self.get_view(), parameter=parameter)
        if parameter == "color":
            self.graphics_item().set_color()

    def add_action(self):
        name = self.__next_terminal_name("outputs/action")
        self.graph._add_action(name.split("/")[-1])
        self.add_terminal(name)

    def add_observation(self):
        name = self.__next_terminal_name("inputs/observation")
        self.graph._add_observation(name.split("/")[-1])
        self.add_terminal(name)

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

    def ctrl_widget(self):
        """Return this Node's control widget.

        By default, Nodes have no control widget. Subclasses may reimplement this
        method to provide a custom widget. This method is called by Flowcharts
        when they are constructing their Node list."""
        return None

    def connected(self, local_term, remote_term):
        """Called whenever one of this node's terminals is connected elsewhere."""
        pass

    def disconnected(self, local_term, remote_term):
        """Called whenever one of this node's terminals is disconnected from another."""
        pass

    def set_exception(self, exc):
        self.exception = exc
        self.recolor()

    def clear_exception(self):
        self.set_exception(None)

    def recolor(self):
        if self.exception is None:
            self.graphics_item().setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        else:
            self.graphics_item().setPen(QtGui.QPen(QtGui.QColor(150, 0, 0), 3))

    def load_state(self, state):
        pos = state["gui_state"].get("pos", (0, 0))
        self.graphics_item().setPos(*pos)

    def save_terminals(self):
        terms = OrderedDict()
        for n, t in self.terminals.items():
            terms[n] = t.save_state()
        return terms

    def clear_terminals(self):
        for t in self.terminals.values():
            t.close()
        self.terminals = OrderedDict()
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()

    def close(self):
        """Cleans up after the node--removes terminals, graphicsItem, widget"""
        self.disconnect_all()
        self.clear_terminals()
        item = self.graphics_item()
        if item.scene() is not None:
            item.scene().removeItem(item)
        self._graphics_item = None
        w = self.ctrl_widget()
        if w is not None:
            w.setParent(None)
        self.sigClosed.emit(self)

    def disconnect_all(self):
        for t in self.terminals.values():
            t.disconnect_all()


class RxGuiNode(QtCore.QObject):
    sigClosed = QtCore.Signal(object)
    sigRenamed = QtCore.Signal(object, object)
    sigTerminalRenamed = QtCore.Signal(object, object)  # term, oldName
    sigTerminalAdded = QtCore.Signal(object, object)  # self, term
    sigTerminalRemoved = QtCore.Signal(object, object)  # self, term

    def __init__(self, name, graph):
        QtCore.QObject.__init__(self)
        self.name = name
        self._graphics_item = None
        self.terminals = OrderedDict()
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()
        self.graph = graph
        self.exception = None

        if self.params()["entity_id"] in ["Actions", "Observations", "Render"]:
            self.node_type = self.params()["entity_id"].lower()
            self.allow_add_terminal = not self.node_type == "render"
            self.allow_remove = False
            self.is_object = False
        else:
            self.node_type = get_yaml_type(self.default_params())
            self.allow_add_terminal = self.is_object = self.node_type == "object"
            self.allow_remove = True
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
                    if self.node_type in ["actions", "observations"]:
                        if terminal in self.default_params()[terminal_type]:
                            continue
                    name = terminal_type + "/" + terminal
                    self.add_terminal(name=name)
                    if self.node_type == "reset_node" and terminal_type == "outputs":
                        name = "feedthroughs/" + terminal
                        self.add_terminal(name=name)

    def params(self):
        return self._get_params(graph_backup=self.graph)

    @exception_handler
    def _get_params(self):
        assert self.name in self.graph._state["nodes"], f" No entity with name '{self.name}' in graph."
        return self.graph._state["nodes"][self.name]["config"]

    def default_params(self):
        return self.graph._state["backup"][self.name]

    def set_param(self, parameter, value):
        self._set_param(parameter, value, graph_backup=self.graph)

    def get_view(self):
        return self.graph.get_view(self.name, depth=["config"])

    @exception_handler
    def _set_param(self, parameter, value):
        self.graph.set(value, self.get_view(), parameter=parameter)
        if parameter == "color":
            self.graphics_item().set_color()

    def remove_terminal(self, term):
        """Remove the specified terminal from this Node. May specify either the
        terminal's name or the terminal itself.

        Causes sigTerminalRemoved to be emitted."""
        if isinstance(term, GuiTerminal):
            name = term.name
        else:
            name = term
            term = self.terminals[name]
        term.close()

        del self.terminals[name]
        if term.is_input:
            del self.inputs[name]
        else:
            del self.outputs[name]

        self.graphics_item().update_terminals()
        self.sigTerminalRemoved.emit(self, term)

    def terminal_renamed(self, term, old_name):
        """Called after a terminal has been renamed

        Causes sigTerminalRenamed to be emitted."""
        new_name = term.name
        for d in [self.terminals, self.inputs, self.outputs]:
            if old_name not in d:
                continue
            d[new_name] = d[old_name]
            del d[old_name]
        gui_state = self.graph._state["gui_state"][self.name]
        if old_name in gui_state["linestyle"]:
            gui_state["linestyle"][new_name] = gui_state["linestyle"][old_name]
            gui_state["linestyle"].pop(old_name)
        self.graphics_item().update_terminals()
        self.sigTerminalRenamed.emit(term, old_name)

    def add_action(self):
        name = self.__next_terminal_name("outputs/action")
        self.graph._add_action(name.split("/")[-1])
        self.add_terminal(name)

    def add_observation(self):
        name = self.__next_terminal_name("inputs/observation")
        self.graph._add_observation(name.split("/")[-1])
        self.add_terminal(name)

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

    def rename(self, name):
        """Rename this node. This will cause sigRenamed to be emitted."""
        self.graph.rename(self.name, name)
        old_name = self.name
        self.name = name
        self.sigRenamed.emit(self, old_name)

    def dependent_nodes(self):
        """Return the list of nodes which provide direct input to this node"""
        nodes = set()
        for t in self.inputs.values():
            nodes |= set([i.node for i in t.input_terminals()])
        return nodes

    def __repr__(self):
        return "<Node %s @%x>" % (self.name, id(self))

    def ctrl_widget(self):
        """Return this Node's control widget.

        By default, Nodes have no control widget. Subclasses may reimplement this
        method to provide a custom widget. This method is called by Flowcharts
        when they are constructing their Node list."""
        return None

    def connected(self, local_term, remote_term):
        """Called whenever one of this node's terminals is connected elsewhere."""
        pass

    def disconnected(self, local_term, remote_term):
        """Called whenever one of this node's terminals is disconnected from another."""
        pass

    def set_exception(self, exc):
        self.exception = exc
        self.recolor()

    def clear_exception(self):
        self.set_exception(None)

    def recolor(self):
        if self.exception is None:
            self.graphics_item().setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        else:
            self.graphics_item().setPen(QtGui.QPen(QtGui.QColor(150, 0, 0), 3))

    def load_state(self, state):
        pos = state["gui_state"].get("pos", (0, 0))
        self.graphics_item().setPos(*pos)

    def save_terminals(self):
        terms = OrderedDict()
        for n, t in self.terminals.items():
            terms[n] = t.save_state()
        return terms

    def clear_terminals(self):
        for t in self.terminals.values():
            t.close()
        self.terminals = OrderedDict()
        self.inputs = OrderedDict()
        self.outputs = OrderedDict()

    def close(self):
        """Cleans up after the node--removes terminals, graphicsItem, widget"""
        self.disconnect_all()
        self.clear_terminals()
        item = self.graphics_item()
        if item.scene() is not None:
            item.scene().removeItem(item)
        self._graphics_item = None
        w = self.ctrl_widget()
        if w is not None:
            w.setParent(None)
        self.sigClosed.emit(self)

    def disconnect_all(self):
        for t in self.terminals.values():
            t.disconnect_all()


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
        if self.node.graph is not None and new_name in self.node.graph.nodes.keys():
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
        for i, t in inp.items():
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
        for i, t in out.items():
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

        if max_width_inp + max_width_out > bounds.width() + 10:
            self.bounds = QtCore.QRectF(0, 0, max_width_inp + max_width_out + 10.0, self.bounds.height())
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
            param_window = ParamWindow(node=self.node)
            param_window.open()
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
        if ev.key() == QtCore.Qt.Key.Key_Delete or ev.key() == QtCore.Qt.Key.Key_Backspace:
            ev.accept()
            if not self.node.allow_remove:
                return
            self.node.graph.remove(self.node.name, remove=False)
            if self.node.name in self.node.graph._state["gui_state"]:
                # Pop node from gui_state upon removal
                self.node.graph._state["gui_state"].pop(self.node.name)
            self.node.close()
        else:
            ev.ignore()

    def itemChange(self, change, val):
        if change == self.GraphicsItemChange.ItemPositionHasChanged:
            self.node.graph._state["gui_state"][self.node.name]["pos"] = [
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

        if self.node.allow_add_terminal:
            if self._node_type == "observations":
                self.menu.addAction("Add observation", self.node.add_observation)
            elif self._node_type == "actions":
                self.menu.addAction("Add action", self.node.add_action)
            else:
                for terminal_type in set.union(
                    configuration.TERMS[self._node_type]["in"],
                    configuration.TERMS[self._node_type]["out"],
                ):
                    if terminal_type in self.node.default_params():
                        terminal_menu = QtWidgets.QMenu("Add {}".format(terminal_type[:-1]), self.menu)
                        for terminal in self.node.default_params()[terminal_type]:
                            terminal_name = terminal_type + "/" + terminal
                            act = terminal_menu.addAction(
                                terminal,
                                partial(
                                    self.add_terminal,
                                    terminal_type=terminal_type,
                                    terminal_name=terminal,
                                ),
                            )
                            if terminal_name in self.node.terminals.keys():
                                act.setEnabled(False)
                            self.menu.addMenu(terminal_menu)
        if self.node.allow_remove:
            self.menu.addAction("Remove {}".format(self.node.name), self.remove_node)

    def add_terminal(self, terminal_type, terminal_name):
        view = self.node.graph.get_view(self.node.name, depth=[terminal_type, terminal_name])
        self.node.graph._add_component(view)
        name = terminal_type + "/" + terminal_name
        self.node.add_terminal(name=name)

    def remove_node(self):
        self.node.graph.remove(self.node.name, remove=False)
        self.node.close()
