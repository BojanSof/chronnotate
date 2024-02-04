import sys

import numpy as np
import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

import gui_resources  # noqa
import settings
from chronnotate_main_window import Ui_main_window as ChronnotateMainWindow
from elements import ColorItemElement, ColorItemModel


class Chronnotate(QMainWindow, ChronnotateMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.init_elements()
        self.init_actions()
        self.init_plots()
        self.data = None

    def init_elements(self):
        self.btn_reset_data.clicked.connect(self.reset_data)
        self.lv_data_columns.doubleClicked.connect(self.update_plot)

    def init_plots(self):
        self.pg_main_plot.setBackground("white")
        self.pg_timeline.setBackground("white")
        self.pg_main_plot.getPlotItem().hideAxis("left")
        self.pg_main_plot.getPlotItem().hideAxis("bottom")
        self.pg_timeline.getPlotItem().hideAxis("left")
        self.pg_timeline.getPlotItem().hideAxis("bottom")
        self.pg_main_plot.clear()
        self.pg_timeline.clear()
        self.pg_main_plot.addLegend()
        self.main_plot_items = {}

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
        model = ColorItemModel(items)
        self.lv_data_columns.setModel(model)

    def update_plot(self, index):
        col = self.lv_data_columns.model().data(
            index, Qt.ItemDataRole.DisplayRole
        )
        color = self.lv_data_columns.model().data(
            index, Qt.ItemDataRole.DecorationRole
        )
        col_active = (
            self.lv_data_columns.model().data(
                index, Qt.ItemDataRole.BackgroundRole
            )
            == settings.LV_DATA_COLUMNS_COLOR_ACTIVE
        )
        if not col_active:
            self.lv_data_columns.model().setData(
                index,
                settings.LV_DATA_COLUMNS_COLOR_ACTIVE,
                Qt.ItemDataRole.BackgroundRole,
            )
            y = self.data[col]
            x = np.arange(len(y))
            self.main_plot_items[col] = self.pg_main_plot.plot(
                x, y, pen=color, name=col
            )
        else:
            self.lv_data_columns.model().setData(
                index,
                settings.LV_DATA_COLUMNS_COLOR_INACTIVE,
                Qt.ItemDataRole.BackgroundRole,
            )
            self.pg_main_plot.removeItem(self.main_plot_items[col])
            del self.main_plot_items[col]

    def reset_data(self):
        self.init_plots()
        for index in range(self.lv_data_columns.model().rowCount()):
            self.lv_data_columns.model().setData(
                self.lv_data_columns.model().index(index, 0),
                settings.LV_DATA_COLUMNS_COLOR_INACTIVE,
                Qt.ItemDataRole.BackgroundRole,
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    chronnotate = Chronnotate()
    chronnotate.show()
    sys.exit(app.exec())
