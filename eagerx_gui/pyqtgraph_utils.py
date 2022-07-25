import inspect
from pyqtgraph.Qt import QtWidgets
from eagerx_gui import configuration
from eagerx.utils.utils import get_attribute_from_module, get_opposite_msg_cls
from eagerx.core.register import REVERSE_REGISTRY, REGISTRY
from typing import Optional, Any
from functools import partial


class ParamWindow(QtWidgets.QDialog):
    def __init__(self, node, term=None):
        self.parent = node.gui.widget().cwWin
        super().__init__(self.parent)
        self.node = node
        self.node_type = node.node_type
        self.library = node.gui.library
        self.is_term = term is not None
        self.entity = term if self.is_term else node
        self.entity_type = "term" if self.is_term else "node"

        name = term.terminal_name if self.is_term else node.name
        self.setWindowTitle("Parameters {}".format(name))

        self.layout = QtWidgets.QGridLayout()
        self.labels = []
        self.widgets = []
        self.params_changed = {}
        row = 0

        self.gui_widgets = configuration.ENGINE_GUI_WIDGETS if self.node_type == "engine_node" else configuration.GUI_WIDGETS
        for key, value in self.entity.params().items():
            if key in self.gui_widgets[self.entity_type]["hide"]["all"]:
                continue
            elif (
                self.node_type in self.gui_widgets[self.entity_type]["hide"]
                and key in self.gui_widgets[self.entity_type]["hide"][self.node_type]
            ):
                continue
            elif (
                self.is_term
                and self.entity.terminal_type in self.gui_widgets[self.entity_type]["hide"]
                and key in self.gui_widgets[self.entity_type]["hide"][self.entity.terminal_type]
            ):
                continue
            elif (
                self.node_type == "engine_node"
                and self.is_term
                and self.entity.node.name == "sensors"
                and key == "external_rate"
            ):
                continue
            else:
                self.add_widget(key, value, row)
                row += 1
        if row == 0:
            label = QtWidgets.QLabel("No parameters to show.")
            self.layout.addWidget(label, row, 0)
        self.setLayout(self.layout)

    def open(self):
        self.exec()

    def add_widget(self, key, value, row):
        label = QtWidgets.QLabel(key)
        if self.is_term and key in ["converter", "processor", "space_converter"] and value is not None:
            button_string = value["converter_type"].split("/")[-1] if "converter_type" in value else "converter"
            widget = QtWidgets.QPushButton(f"{button_string}")
            is_space_converter = key == "space_converter"
            widget.pressed.connect(partial(self.open_converter_dialog, is_space_converter=is_space_converter))
        else:
            widget = QtWidgets.QLabel(str(value))
        for grid_object in [label, widget]:
            font = grid_object.font()
            font.setPointSize(12)
            grid_object.setFont(font)
        for grid_object in [label, widget]:
            font = grid_object.font()
            font.setPointSize(12)
            grid_object.setFont(font)
        self.layout.addWidget(label, row, 0)
        self.layout.addWidget(widget, row, 1)
        self.labels.append(label)

        self.widgets.append(widget)

    def open_converter_dialog(self, is_space_converter=False):
        key = "space_converter" if is_space_converter else "converter"
        library = self.node.gui.library
        if "converter" in self.entity.params() and self.entity.params()["converter"] is not None:
            msg_type = get_opposite_msg_cls(self.entity.params()["msg_type"], self.entity.params()["converter"])
        else:
            msg_type = get_attribute_from_module(self.entity.params()["msg_type"])
        msg_type_in, msg_type_out = (msg_type, None) if self.entity.is_input else (None, msg_type)
        is_space_converter = is_space_converter or self.node.node_type in [
            "actions",
            "observations",
        ]
        converter_dialog = ConverterDialog(
            converter=self.entity.params()[key],
            parent=self.parent,
            library=library,
            msg_type_in=msg_type_in,
            msg_type_out=msg_type_out,
            is_space_converter=is_space_converter,
        )
        converter_dialog.exec()

class ConverterDialog(QtWidgets.QDialog):
    def __init__(
        self,
        converter,
        parent,
        library,
        msg_type_in,
        msg_type_out=None,
        is_space_converter=False,
    ):
        super().__init__(parent)
        self.parent = parent
        self.msg_type_in = msg_type_in
        self.msg_type_out = msg_type_out
        self.is_space_converter = is_space_converter
        self.converter = converter
        self.library = library
        self.setWindowTitle("Converter Parameters")
        self.layout = QtWidgets.QGridLayout()
        self.labels = []
        self.widgets = []

        converter_class = get_attribute_from_module(self.converter["converter_type"])
        converter_id = REVERSE_REGISTRY[converter_class.spec]
        (
            converter_id,
            required_args,
            optional_args,
        ) = self.get_parameters(converter_id)

        self.add_widget(
            key="Converter Class",
            value=converter_id,
            parameter=None,
            row=0,
        )
        self.add_argument_widgets(required_args, optional_args)
        self.setLayout(self.layout)

    def add_argument_widgets(self, required_args, optional_args):
        row = 1
        required_args_label = QtWidgets.QLabel("Required Converter Arguments")
        self.layout.addWidget(required_args_label, row, 0)
        self.labels.append(required_args_label)
        row += 1

        for key, parameter in required_args.items():
            if key in self.converter:
                value = self.converter[key]
            else:
                value = None
            self.add_widget(key, value, parameter, row)
            row += 1

        optional_args_label = QtWidgets.QLabel("Optional Converter Arguments")
        self.layout.addWidget(optional_args_label, row, 0)
        self.labels.append(optional_args_label)
        row += 1

        for key, parameter in optional_args.items():
            if key in self.converter:
                value = self.converter[key]
            else:
                value = parameter.default
            self.add_widget(key, value, parameter, row)
            row += 1

    def get_parameters(self, converter_id):
        available_converters = {}
        required_args = {}
        optional_args = {}

        if self.is_space_converter:
            cnvrtr_types = ["SpaceConverter"]
        elif None in [self.msg_type_in, self.msg_type_out]:
            cnvrtr_types = ["BaseConverter", "Processor", "Converter"]
        elif self.msg_type_in == self.msg_type_out:
            cnvrtr_types = ["BaseConverter", "Processor"]
        else:
            cnvrtr_types = ["Converter"]

        for cnvrtr_type in cnvrtr_types:
            if cnvrtr_type not in self.library:
                continue
            for cnvrtr in self.library[cnvrtr_type]:
                cnvrtr_cls = cnvrtr["cls"]
                available_converters[cnvrtr["entity_id"]] = {
                    "spec": inspect.signature(REGISTRY[cnvrtr["entity_cls"]][cnvrtr["entity_id"]]["spec"]),
                    "cls": cnvrtr_cls,
                }
                # Add initial_obs
                if cnvrtr_type == "SpaceConverter":
                    if "initial_obs" not in available_converters[cnvrtr["entity_id"]]["spec"].parameters.keys():
                        arg_initial_obs = inspect.Parameter(
                            "initial_obs", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Optional[Any], default=None
                        )
                        sig = available_converters[cnvrtr["entity_id"]]["spec"]
                        sig = sig.replace(parameters=tuple(sig.parameters.values()) + (arg_initial_obs,))
                        available_converters[cnvrtr["entity_id"]]["spec"] = sig

        parameters = available_converters[converter_id]["spec"].parameters
        for key in parameters.keys():
            if key == "spec":
                continue
            if parameters[key].default is inspect._empty:
                required_args[key] = parameters[key]
            else:
                optional_args[key] = parameters[key]
        for key in self.converter.keys():
            if key not in parameters.keys():
                if key == "initial_obs":
                    continue

        return converter_id, required_args, optional_args

    def add_widget(self, key, value, parameter, row):
        if parameter is not None:
            label = QtWidgets.QLabel(str(parameter).split("=")[0].strip())
        else:
            label = QtWidgets.QLabel(str(key))
        widget = QtWidgets.QLabel(str(value))

        self.layout.addWidget(label, row, 0)
        self.layout.addWidget(widget, row, 1)
        self.labels.append(label)
        self.widgets.append(widget)
