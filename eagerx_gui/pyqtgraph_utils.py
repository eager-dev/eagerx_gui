from pyqtgraph.Qt import QtWidgets
from functools import partial


class ParamWindow(QtWidgets.QDialog):
    def __init__(self, spec, parent, filter=[]):
        self.parent = parent
        super().__init__(self.parent)

        self.spec = spec
        self.setWindowTitle(f"Parameters {spec._name}.{'.'.join(spec._depth)}")

        self.layout = QtWidgets.QGridLayout()
        self.labels = []
        self.widgets = []
        row = 0

        for key, value in spec.to_dict().items():
            if key in filter:
                continue
            self.add_widget(key, value, row)
            row += 1
        if row == 0:
            label = QtWidgets.QLabel("No parameters to show.")
            self.layout.addWidget(label, row, 0)
        self.setLayout(self.layout)

    def add_widget(self, key, value, row):
        label = QtWidgets.QLabel(key)
        if type(value) is dict:
            spec = getattr(self.spec, key)

            widget = QtWidgets.QPushButton(f"Inspect {spec._name}.{'.'.join(spec._depth)}")
            widget.pressed.connect(partial(self.open_dict_dialog, key=key))
        else:
            # widget = QtWidgets.QLabel(str(value))
            widget = QtWidgets.QLineEdit(str(value))
            widget.setReadOnly(True)
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

    def open_dict_dialog(self, key):
        dialog = ParamWindow(
            spec=getattr(self.spec, key),
            parent=self.parent,
        )
        dialog.exec()
