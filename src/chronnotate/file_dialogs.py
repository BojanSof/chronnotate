from PyQt6 import QtGui
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
)


class OpenDialog(QDialog):
    def __init__(self, default_label_column_name="Label"):
        super().__init__()

        self.setWindowTitle("File settings")
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(":/icons/resources/icon.ico"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.Off,
        )
        self.setWindowIcon(icon)

        layout = QGridLayout()

        skip_lines_label = QLabel("Skip Lines:")
        layout.addWidget(skip_lines_label, 0, 0)

        self.skip_lines_spinbox = QSpinBox()
        self.skip_lines_spinbox.setMinimum(0)  # Minimum value for the spinbox
        layout.addWidget(self.skip_lines_spinbox, 0, 1)

        label_column_name_label = QLabel("Label Column Name:")
        layout.addWidget(label_column_name_label, 1, 0)

        self.label_column_name_edit = QLineEdit(default_label_column_name)
        layout.addWidget(self.label_column_name_edit, 1, 1)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button, 2, 0, 1, 2)

        self.setLayout(layout)

    def get_skip_lines(self):
        return self.skip_lines_spinbox.value()

    def get_label_column_name(self):
        return self.label_column_name_edit.text()
