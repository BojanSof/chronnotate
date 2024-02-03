import sys

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

import gui_resources  # noqa
from chronnotate_main_window import Ui_main_window as ChronnotateMainWindow
from elements import ColorItemElement, ColorItemModel


class Chronnotate(QMainWindow, ChronnotateMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.init_elements()
        self.init_actions()

    def init_elements(self):
        self.pg_main_plot.setBackground("white")
        self.pg_timeline.setBackground("white")
        self.pg_main_plot.getPlotItem().hideAxis("left")
        self.pg_main_plot.getPlotItem().hideAxis("bottom")
        self.pg_timeline.getPlotItem().hideAxis("left")
        self.pg_timeline.getPlotItem().hideAxis("bottom")
        self.lv_data_columns.clicked.connect(self.update_plot)

    def init_actions(self):
        self.action_open_file.triggered.connect(self.open_file)
        self.action_exit.triggered.connect(self.close)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select file with time-series data to load",
            "",
            "All files (*);;CSV (*csv);;Text files (*txt)",
        )
        if path != "":
            self.load_file(path)

    def load_file(self, path):
        try:
            data = pd.read_csv(path)
            self.fill_elements_from_data(data)
        except Exception:
            QMessageBox.critical(
                self, "File error", f"Could not load file {path}"
            )

    def fill_elements_from_data(self, data: pd.DataFrame):
        self.data = data
        items = [ColorItemElement(col) for col in self.data.columns]
        self.data_columns_model = ColorItemModel(items)
        self.lv_data_columns.setModel(self.data_columns_model)

    def update_plot(self, index):
        col = self.data_columns_model.data(index, Qt.ItemDataRole.DisplayRole)
        y = self.data[col]
        x = np.arange(len(y))
        self.pg_main_plot.clear()
        self.pg_main_plot.plot(x, y, pen="b", name=col)
        self.pg_main_plot.setLabel("left", col)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    chronnotate = Chronnotate()
    chronnotate.show()
    sys.exit(app.exec())
