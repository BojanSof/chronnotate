import sys

import numpy as np
import pandas as pd
import pyqtgraph as pg
from pandas.api.types import is_numeric_dtype
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
)

from . import gui_resources, settings  # noqa
from .chronnotate_main_window import Ui_main_window as ChronnotateMainWindow
from .data_utils import find_subsegments
from .elements import AnnotationRegion, ColorItemElement, ColorItemModel
from .file_dialogs import OpenDialog


class Chronnotate(QMainWindow, ChronnotateMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.init_elements()
        self.init_plots()
        self.init_labels()
        self.init_actions()
        self.data = None

    def init_elements(self):
        self.btn_deselect_all.clicked.connect(self.plot_deselect_all)
        self.btn_create_label.clicked.connect(lambda: self.create_label(None))
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

        self.annotation_regions = []
        self.pg_main_plot.set_annotation_regions_requirements(
            self.annotation_regions, self.lv_labels
        )

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
        model.dataChanged.connect(self.update_annotation_regions_labels)
        self.lv_labels.setModel(model)
        self.label_counter = 1

    def init_actions(self):
        self.action_open_file.triggered.connect(self.open_file)
        self.action_save_file.triggered.connect(self.save_file)
        self.action_exit.triggered.connect(self.close)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select file with time-series data to load",
            "",
            "All files (*);;CSV (*csv);;Text files (*txt)",
        )
        if path != "":
            settings_dialog = OpenDialog()
            if settings_dialog.exec() == QDialog.DialogCode.Accepted:
                skip_lines = settings_dialog.get_skip_lines()
                col_label = settings_dialog.get_label_column_name()
                self.load_file(path, skip_lines, col_label)

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Select output file to save annotated data",
            "",
            "All files (*);;CSV (*csv);;Text files (*txt)",
        )
        if path != "":
            labeled_data = self.create_labeled_data()
            labeled_data.to_csv(path, index=False)

    def load_file(self, path, skip_lines, col_label):
        try:
            data = pd.read_csv(path, skiprows=skip_lines)
            if len(col_label) > 0:
                self.label_column = col_label
            else:
                self.label_column = settings.DEFAULT_LABEL_COLUMN
            self.fill_elements_from_data(data)
        except Exception:
            QMessageBox.critical(
                self, "File error", f"Could not load file {path}"
            )

    def create_labeled_data(self):
        labels = pd.Series(["" for _ in range(len(self.data))]).astype(
            "string"
        )
        for region in self.annotation_regions:
            start, end = region.getRegion()
            start = int(np.rint(start))
            end = int(np.rint(end))
            label = region.label
            labels[start:end] = label
        labeled_data = self.data.copy()
        labeled_data[self.label_column] = labels
        return labeled_data

    def fill_elements_from_data(self, data: pd.DataFrame):
        self.data = data
        items = [
            ColorItemElement(col)
            for col in self.data.columns
            if is_numeric_dtype(self.data[col]) and col != self.label_column
        ]
        model = ColorItemModel(items)
        self.lv_data_columns.setModel(model)
        if self.label_column in self.data.columns:
            segments = find_subsegments(self.data, self.label_column)
            labels = self.data[self.label_column].dropna().unique()
            label_colors = {}
            for label in labels:
                item = self.create_label(label)
                label_colors[label] = item.color
            for segment in segments:
                rgn = AnnotationRegion(
                    self.pg_main_plot,
                    segment["label"],
                    label_colors[segment["label"]],
                    (segment["start"], segment["end"]),
                )
                self.pg_main_plot.plotItem.vb.sigYRangeChanged.connect(
                    rgn.update_label_pos
                )
                rgn.select(True)
                rgn.update_visible(False)
                self.annotation_regions.append(rgn)

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
                for rgn in self.annotation_regions:
                    rgn.update_visible(True)
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
                for rgn in self.annotation_regions:
                    rgn.update_visible(False)

    def plot_deselect_all(self):
        for i in range(self.lv_data_columns.model().rowCount()):
            index = self.lv_data_columns.model().createIndex(i, 0)
            col_active = (
                self.lv_data_columns.model().data(
                    index, Qt.ItemDataRole.BackgroundRole
                )
                == settings.LV_DATA_COLUMNS_COLOR_ACTIVE
            )
            if col_active:
                self.lv_data_columns.model().setData(
                    index,
                    settings.LV_DATA_COLUMNS_COLOR_INACTIVE,
                    Qt.ItemDataRole.BackgroundRole,
                )
                col = self.lv_data_columns.model().data(
                    index, Qt.ItemDataRole.DisplayRole
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
        for rgn in self.annotation_regions:
            rgn.update_visible(False)

    def create_label(self, label=None):
        lbl_name = f"Label {self.label_counter}" if label is None else label
        self.label_counter += 1
        item = ColorItemElement(lbl_name)
        model = self.lv_labels.model()
        model.insertItem(item)
        index = model.createIndex(model.rowCount() - 1, 0)
        if label is None:
            self.lv_labels.edit(index)
        return item

    def delete_label(self):
        model = self.lv_labels.model()
        removing = True
        while removing:
            indexes = self.lv_labels.selectedIndexes()
            if len(indexes) == 0:
                removing = False
            else:
                label = model.data(indexes[0], Qt.ItemDataRole.DisplayRole)
                model.removeItem(indexes[0].row())
                regions_to_remove = []
                for annotation_region in self.annotation_regions:
                    labels = annotation_region.label.split(
                        settings.LABEL_SEPARATOR
                    )
                    if label in labels:
                        regions_to_remove.append(annotation_region)
                for region in regions_to_remove:
                    region.remove()
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

    def update_annotation_regions_labels(self, index, _):
        model = self.lv_labels.model()
        old_label = model.items[index.row()].prev_label
        new_label = model.data(index, Qt.ItemDataRole.DisplayRole)
        for region in self.annotation_regions:
            labels = region.label.split(settings.LABEL_SEPARATOR)
            labels = [lab if lab != old_label else new_label for lab in labels]
            label = settings.LABEL_SEPARATOR.join(labels)
            region.update_label(label)

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
        return super().eventFilter(obj, event)


def main():
    app = QApplication(sys.argv)
    chronnotate = Chronnotate()
    chronnotate.show()
    sys.exit(app.exec())
