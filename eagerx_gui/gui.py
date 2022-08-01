"""
 Adapted from https://github.com/pyqtgraph/pyqtgraph/blob/master/pyqtgraph/flowchart/Flowchart.py
"""

# Import pyqtgraph modules
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph.Qt import QtCore, QtWidgets
from pyqtgraph import dockarea
from pyqtgraph.debug import printExc

# eagerx imports
from eagerx.core.graph import Graph
from eagerx.core.graph_engine import EngineGraph

# eagerx_gui imports
from eagerx_gui import configuration
from eagerx_gui.utils import add_pos_to_state
from eagerx_gui import gui_view
from eagerx_gui.gui_node import RxGuiNode, NodeGraphicsItem
from eagerx_gui.gui_terminal import TerminalGraphicsItem, ConnectionItem


class Gui(QtCore.QObject):
    def __init__(self, state, is_engine=False):
        super().__init__()
        self.graph = Graph(state=state) if not is_engine else EngineGraph(state=state)
        self.is_engine = is_engine
        self.nodes = {}
        self.next_z_val = 10
        self._widget = None
        self.scene = None
        self.file_path = None
        self.widget()
        self.load_state()
        self.viewBox.autoRange(padding=0.04)

    def create_node(self, name, pos):
        """Create a new Node and add it to this flowchart."""
        node = RxGuiNode(name, gui=self)
        self.add_node(node, name, pos)
        return node

    def add_node(self, node, name, pos=None):
        """Add an existing Node to this flowchart.

        See also: createnode
        """
        if pos is None:
            pos = [0, 0]
        if type(pos) in [QtCore.QPoint, QtCore.QPointF]:
            pos = [pos.x(), pos.y()]
        item = node.graphics_item()
        item.setZValue(self.next_z_val * 2)
        self.next_z_val += 1
        self.viewBox.addItem(item)
        item.moveBy(*pos)
        self.nodes[name] = node

    def connect_terminals(self, term1, term2):
        """Connect two terminals together within this flowchart."""
        connection_item = ConnectionItem(term1.graphics_item(), term2.graphics_item())
        term1.graphics_item().getViewBox().addItem(connection_item)

        term1.connections[term2] = connection_item
        term2.connections[term1] = connection_item

        term1.connected(term2)
        term2.connected(term1)

    def chart_graphics_item(self):
        """Return the graphicsItem that displays the internal nodes and
        connections of this flowchart.

        Note that the similar method `graphicsItem()` is inherited from Node
        and returns the *external* graphical representation of this flowchart."""
        return self.viewBox

    def widget(self):
        """Return the control widget for this flowchart.

        This widget provides GUI access to the parameters for each node and a
        graphical representation of the flowchart.
        """
        if self._widget is None:
            self._widget = EagerxGraphWidget(self)
            self.scene = self._widget.scene
            self.viewBox = self._widget.viewBox()
        return self._widget

    def load_state(self):
        self.blockSignals(True)
        try:
            add_pos_to_state(self.graph._state, is_engine=self.is_engine)
            nodes = self.graph._state["nodes"]
            nodes = [dict(**node, name=name, gui_state=self.graph._state["gui_state"][name]) for name, node in nodes.items()]
            nodes.sort(key=lambda a: a["gui_state"]["pos"][0])
            for n in nodes:
                if n["name"] in self.nodes:
                    self.nodes[n["name"]].load_state(n)
                    continue
                try:
                    name = n["name"]
                    pos = n["gui_state"]["pos"]
                    node = self.create_node(name, pos)
                    node.load_state(n)
                except Exception:
                    printExc("Error creating node %s: (continuing anyway)" % n["name"])

            connects = [
                (
                    connection[0][0],
                    "/".join(connection[0][1:3]),
                    connection[1][0],
                    "/".join(connection[1][1:3]),
                )
                for connection in self.graph._state["connects"]
            ]
            for n1, t1, n2, t2 in connects:
                try:
                    self.connect_terminals(self.nodes[n1].terminals[t1], self.nodes[n2].terminals[t2])
                except Exception:
                    print(self.nodes[n1].terminals)
                    print(self.nodes[n2].terminals)
                    printExc("Error connecting terminals %s.%s - %s.%s:" % (n1, t1, n2, t2))

        finally:
            self.blockSignals(False)

    def tuple_to_view(self, t):
        if isinstance(t, tuple):
            t = list(t)
        return self.graph.get_view(t[0], depth=t[1:])


class GraphicsItem(GraphicsObject):
    def __init__(self, chart):
        GraphicsObject.__init__(self)
        self.chart = chart  # chart is an instance of Flowchart()
        self.update_terminals()

    def update_terminals(self):
        self.terminals = {}

    def boundingRect(self):
        return QtCore.QRectF()

    def paint(self, p, *args):
        pass


class EagerxGraphWidget(dockarea.DockArea):
    """Includes the actual graphical flowchart and debugging interface"""

    def __init__(self, chart):
        dockarea.DockArea.__init__(self)
        self.chart = chart
        self.cwWin = QtWidgets.QMainWindow()
        self.cwWin.setWindowTitle("EAGERx EngineGraph")
        self.cwWin.setCentralWidget(self)
        self.cwWin.resize(1000, 800)
        self.hoverItem = None

        # build user interface (it was easier to do it here than via developer)
        self.view = gui_view.RxView(self)
        self.viewDock = dockarea.Dock("view", size=(1000, 600))
        self.viewDock.addWidget(self.view)
        self.viewDock.hideTitleBar()
        self.addDock(self.viewDock)

        self.hoverText = QtWidgets.QTextEdit()
        self.hoverText.setReadOnly(True)
        self.hoverDock = dockarea.Dock("Hover Info", size=(1000, 20))
        self.hoverDock.addWidget(self.hoverText)
        self.addDock(self.hoverDock, "bottom")

        self.scene = self.view.scene()
        self._viewBox = self.view.viewBox()
        self.scene.sigMouseHover.connect(self.hover_over)

    def menuPosChanged(self, pos):
        self.menuPos = pos

    def showViewMenu(self, ev):
        self.buildMenu(ev.scenePos())
        self.nodeMenu.popup(ev.screenPos())

    def viewBox(self):
        return self._viewBox  # the viewBox that items should be added to

    def hover_over(self, items):
        for item in items:
            self.hoverItem = item
            if hasattr(item, "term") and isinstance(item, TerminalGraphicsItem):
                text = "name: " + item.term.terminal_name
                for key, value in item.term.params().items():
                    if key in configuration.GUI_WIDGETS["term"]["hide"]["all"]:
                        continue
                    elif (
                        item.term.node_type in configuration.GUI_WIDGETS["term"]["hide"]
                        and key in configuration.GUI_WIDGETS["term"]["hide"][item.term.node_type]
                    ):
                        continue
                    elif (
                        item.term.terminal_type in configuration.GUI_WIDGETS["term"]["hide"]
                        and key in configuration.GUI_WIDGETS["term"]["hide"][item.term.terminal_type]
                    ):
                        continue
                    text += "\n" + "{}: {}".format(key, value)
                self.hoverText.setPlainText(text)
                return
            elif hasattr(item, "node") and isinstance(item, NodeGraphicsItem):
                text = ""
                for key, value in item.node.params().items():
                    if key in configuration.GUI_WIDGETS["node"]["hide"]["all"]:
                        continue
                    elif (
                        item.node.node_type in configuration.GUI_WIDGETS["node"]["hide"]
                        and key in configuration.GUI_WIDGETS["node"]["hide"][item.node.node_type]
                    ):
                        continue
                    text += "{}: {}\n".format(key, value)
                self.hoverText.setPlainText(text)
                return
        self.hoverText.setPlainText("")
