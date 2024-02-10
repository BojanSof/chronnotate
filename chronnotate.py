import sys

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
)

import gui_resources  # noqa
import settings
from chronnotate_main_window import Ui_main_window as ChronnotateMainWindow
from elements import ColorItemElement, ColorItemModel


class Chronnotate(QMainWindow, ChronnotateMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.init_elements()
        self.init_plots()
        self.init_labels()
        self.init_actions()
        self.data = None
        self.labels = []

    def init_elements(self):
        self.btn_reset_data.clicked.connect(self.reset_data)
        self.btn_create_label.clicked.connect(self.create_label)
        self.btn_delete_label.clicked.connect(self.delete_label)
        self.lv_data_columns.doubleClicked.connect(self.update_plot)
        self.lv_data_columns.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.lv_labels.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
        )
        self.lv_labels.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.lv_labels.viewport().installEventFilter(self)
        self.pg_timeline.setMenuEnabled(False)
        self.pg_timeline.setMouseEnabled(x=False, y=False)
        self.pg_main_plot.hideButtons()

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
        self.timeline_plot_items = {}

    def init_labels(self):
        items = []
        model = ColorItemModel(items)
        self.lv_labels.setModel(model)

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
            self.timeline_plot_items[col] = self.pg_timeline.plot(
                x, y, pen=color
            )
            if len(self.timeline_plot_items.keys()) == 1:
                # add range view
                range_len = len(y) / 10
                self.timeline_plot_range = pg.LinearRegionItem([0, range_len])
                self.timeline_plot_range.setZValue(-10)
                self.timeline_plot_range.setBounds([0, len(y)])
                self.timeline_plot_range.sigRegionChanged.connect(
                    self.update_plot_from_range
                )
                self.pg_timeline.addItem(self.timeline_plot_range)
                self.pg_main_plot.sigRangeChanged.connect(
                    self.update_range_from_plot
                )
                self.update_plot_from_range()
        else:
            self.lv_data_columns.model().setData(
                index,
                settings.LV_DATA_COLUMNS_COLOR_INACTIVE,
                Qt.ItemDataRole.BackgroundRole,
            )
            self.pg_main_plot.removeItem(self.main_plot_items[col])
            del self.main_plot_items[col]
            self.pg_timeline.removeItem(self.timeline_plot_items[col])
            del self.timeline_plot_items[col]
            if len(self.timeline_plot_items.keys()) == 0:
                # remove range view
                self.pg_timeline.removeItem(self.timeline_plot_range)
                self.pg_main_plot.sigRangeChanged.disconnect()
                self.timeline_plot_range.sigRegionChanged.disconnect()

    def reset_data(self):
        self.init_plots()
        for index in range(self.lv_data_columns.model().rowCount()):
            self.lv_data_columns.model().setData(
                self.lv_data_columns.model().index(index, 0),
                settings.LV_DATA_COLUMNS_COLOR_INACTIVE,
                Qt.ItemDataRole.BackgroundRole,
            )

    def create_label(self):
        lbl_name = "Label"
        item = ColorItemElement(lbl_name)
        model = self.lv_labels.model()
        model.insertItem(item)
        index = model.createIndex(model.rowCount() - 1, 0)
        self.lv_labels.edit(index)

    def delete_label(self):
        model = self.lv_labels.model()
        removing = True
        while removing:
            indexes = self.lv_labels.selectedIndexes()
            if len(indexes) == 0:
                removing = False
            else:
                model.removeItem(indexes[0].row())
        self.lv_labels.clearSelection()
        self.lv_labels.setCurrentIndex(model.createIndex(-1, -1))

    def update_plot_from_range(self):
        self.pg_main_plot.setXRange(
            *self.timeline_plot_range.getRegion(), padding=0
        )

    def update_range_from_plot(self):
        self.timeline_plot_range.setRegion(
            self.pg_main_plot.getViewBox().viewRange()[0]
        )

    def eventFilter(self, obj, event: QEvent):
        if (
            obj == self.lv_labels.viewport()
            and event.type() == QEvent.Type.MouseButtonPress
        ):
            index = self.lv_labels.indexAt(event.pos())
            if not index.isValid():
                self.lv_labels.clearSelection()
                self.lv_labels.setCurrentIndex(
                    self.lv_labels.model().createIndex(-1, -1)
                )
                return True
        # elif obj == self.pg_main_plot.viewport():
        #     if (
        #         event.type() == QEvent.Type.MouseButtonPress
        #         and event.button() == Qt.MouseButton.LeftButton
        #     ):
        #         return True
        #     elif event.type() == QEvent.Type.GraphicsSceneMouseMove:
        #         event.accept()
        #         if event.button() == Qt.MouseButton.LeftButton:
        #             if event.isStart():
        #                 print("start")
        #             elif event.isFinish():
        #                 print("done")
        #             return True
        return super().eventFilter(obj, event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    chronnotate = Chronnotate()
    chronnotate.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    chronnotate = Chronnotate()
    chronnotate.show()
    sys.exit(app.exec())
