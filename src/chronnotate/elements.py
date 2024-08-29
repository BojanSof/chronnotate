import string

import pyqtgraph as pg
from PyQt6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    QVariant,
    pyqtSignal,
)
from PyQt6.QtGui import QColor

from .settings import LABEL_SEPARATOR
from .utils import SignalBlocker


class ColorItemElement:
    __COLORS = [
        "#4E79A7",
        "#F28E2C",
        "#E15759",
        "#76B7B2",
        "#59A14F",
        "#EDC949",
        "#AF7AA1",
        "#FF9DA7",
        "#9C755F",
        "#BAB0AC",
        "#A9A9A9",
        "#6495ED",
        "#DC143C",
        "#00FFFF",
        "#00008B",
        "#008B8B",
        "#B8860B",
        "#A9A9A9",
        "#006400",
        "#8B008B",
        "#556B2F",
        "#8B0000",
        "#FF8C00",
        "#9932CC",
        "#8B0000",
        "#E9967A",
        "#8FBC8F",
        "#483D8B",
        "#2F4F4F",
        "#00CED1",
        "#9400D3",
        "#FF1493",
        "#00BFFF",
        "#696969",
        "#696969",
        "#1E90FF",
        "#B22222",
        "#FFFAF0",
        "#228B22",
        "#FF00FF",
        "#DCDCDC",
        "#F8F8FF",
        "#FFD700",
        "#DAA520",
        "#808080",
        "#008000",
        "#ADFF2F",
        "#808080",
        "#F0FFF0",
        "#FF69B4",
        "#CD5C5C",
        "#4B0082",
        "#FFFFF0",
        "#F0E68C",
        "#E6E6FA",
        "#FFF0F5",
        "#7CFC00",
        "#FFFACD",
        "#ADD8E6",
        "#F08080",
        "#E0FFFF",
        "#FAFAD2",
        "#D3D3D3",
        "#90EE90",
        "#D3D3D3",
        "#FFB6C1",
        "#FFA07A",
        "#20B2AA",
        "#87CEFA",
        "#778899",
        "#778899",
        "#B0C4DE",
        "#FFFFE0",
        "#00FF00",
        "#32CD32",
        "#FAF0E6",
        "#FF00FF",
        "#800000",
        "#66CDAA",
        "#0000CD",
        "#BA55D3",
        "#9370DB",
        "#3CB371",
        "#7B68EE",
        "#00FA9A",
        "#48D1CC",
        "#C71585",
        "#191970",
        "#F5FFFA",
        "#FFE4E1",
        "#FFE4B5",
        "#FFDEAD",
        "#000080",
        "#FDF5E6",
        "#808000",
        "#6B8E23",
        "#FFA500",
        "#FF4500",
        "#DA70D6",
        "#EEE8AA",
        "#98FB98",
        "#AFEEEE",
        "#DB7093",
        "#FFEFD5",
        "#FFDAB9",
        "#CD853F",
        "#FFC0CB",
        "#DDA0DD",
        "#B0E0E6",
        "#800080",
        "#663399",
        "#FF0000",
        "#BC8F8F",
        "#4169E1",
        "#8B4513",
        "#FA8072",
        "#F4A460",
        "#2E8B57",
        "#FFF5EE",
        "#A0522D",
        "#C0C0C0",
        "#87CEEB",
        "#6A5ACD",
        "#708090",
        "#708090",
        "#FFFAFA",
        "#00FF7F",
        "#4682B4",
        "#D2B48C",
        "#008080",
        "#D8BFD8",
        "#FF6347",
        "#40E0D0",
        "#EE82EE",
        "#F5DEB3",
        "#FFFFFF",
        "#F5F5F5",
        "#FFFF00",
        "#9ACD32",
    ]
    __i_COLORS = 0

    def __init__(self, label, color=None):
        if (
            color is not None
            and not isinstance(color, tuple)
            and not isinstance(color, str)
        ):
            raise ValueError("color must be tuple or string")
        if isinstance(color, tuple) and (
            len(tuple) != 4 or any(c < 0 or c > 255 for c in color)
        ):
            raise ValueError(
                "color must be tuple of shape (4, )"
                "in format (red, green, blue, alpha)"
                "with each channel in range [0, 255]"
            )
        elif isinstance(color, str) and (
            len(str) != 9 or not all(c in string.hexdigits for c in str)
        ):
            raise ValueError("color must be valid RGB or RGBA hex string")

        self.label = label
        self.prev_label = None
        if color is None:
            self.color = ColorItemElement.__COLORS[ColorItemElement.__i_COLORS]
            ColorItemElement.__i_COLORS = (
                ColorItemElement.__i_COLORS + 1
            ) % len(ColorItemElement.__COLORS)
        elif isinstance(color, tuple):
            r, g, b, a = color
            self.color = f"#{r:02x}{g:02x}{b:02x}{a:02x}"
        else:
            self.color = color
        self.color = QColor(self.color)
        self.bg_color = QColor("transparent")

    def __repr__(self):
        return f"(label {self.label}, color {self.color})"


class ColorItemModel(QAbstractListModel):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def rowCount(self, parent=QModelIndex()):
        return len(self.items)

    def data(self, index, role):
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return QVariant()
        item = self.items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return item.label
        elif role == Qt.ItemDataRole.DecorationRole:
            return item.color
        elif role == Qt.ItemDataRole.BackgroundRole:
            return item.bg_color

    def setData(self, index, value, role):
        if not index.isValid() or not (0 <= index.row() < len(self.items)):
            return False
        item = self.items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            if not isinstance(value, str):
                raise ValueError("value must be string for DisplayRole")
            item.label = value
        elif role == Qt.ItemDataRole.DecorationRole:
            if not isinstance(value, QColor):
                raise ValueError("value must be QColor for DecorationRole")
            item.color = value
        elif role == Qt.ItemDataRole.BackgroundRole:
            if not isinstance(value, QColor):
                raise ValueError("value must be QColor for BackgroundRole")
            item.bg_color = value
        elif role == Qt.ItemDataRole.EditRole:
            if len(value) > 0:
                item.prev_label = item.label
                item.label = value
        # emit dataChanged signal, must be done manually
        self.dataChanged.emit(index, index, [])
        return True

    def insertItem(self, item):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.items.append(item)
        self.endInsertRows()

    def insertItemAt(self, index, item):
        if not (0 <= index < len(self.items)):
            return False
        self.beginInsertRows(QModelIndex(), index, index)
        self.items.insert(index, item)
        self.endInsertRows()
        return True

    def removeItem(self, index):
        if not (0 <= index < len(self.items)):
            return False
        self.beginRemoveRows(QModelIndex(), index, index)
        del self.items[index]
        self.endRemoveRows()

    def flags(self, index):
        flags = super().flags(index)
        if index.isValid():
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags


class AnnotationRegion(pg.LinearRegionItem):
    regionChangeFinished = pyqtSignal(object)
    gotSelected = pyqtSignal(object)
    removeRequested = pyqtSignal(object)

    def __init__(self, plot_widget, label, color, values):
        super().__init__(
            values=values,
            orientation="vertical",
            movable=True,
            swapMode="sort",
            bounds=(0, 1e9),
        )
        self.setZValue(0)

        self.plot_widget = plot_widget
        self.sigRegionChangeFinished.connect(self.region_changed)
        self.label = label
        self.old_onset = values[0]
        self.selected = False

        self.base_color = color
        self.hover_color = color.darker(75)
        self.text_color = color.darker(150)
        self.base_color.setAlpha(75)
        self.hover_color.setAlpha(150)
        self.text_color.setAlpha(255)

        self.label_item = pg.TextItem(text=label, anchor=(0.5, 0.5))
        self.sigRegionChanged.connect(self.update_label_pos)

        self.update_color()
        self.update_label_pos()
        self.plot_widget.addItem(self, ignoreBounds=True)
        self.plot_widget.addItem(self.label_item, ignoreBounds=True)

    def setRegion(self, region):
        pg.LinearRegionItem.setRegion(self, region)
        self.update_label_pos()

    def region_changed(self):
        self.regionChangeFinished.emit(self)
        self.update_label_pos()

    def update_color(self):
        kwargs = dict(color=self.hover_color, width=2)
        self.line_pen = pg.mkPen(**kwargs)
        self.hover_pen = pg.mkPen(color=self.text_color, width=2)
        self.setBrush(self.base_color)
        self.setHoverBrush(self.hover_color)
        self.label_item.setColor(self.text_color)
        for line in self.lines:
            line.setPen(self.line_pen)
            line.setHoverPen(self.hover_pen)
        self.update()

    def update_label(self, label):
        self.label = label
        self.label_item.setText(label)
        self.label_item.update()

    def update_label_pos(self):
        rgn = self.getRegion()
        vb = self.plot_widget.plotItem.vb
        if vb:
            yvb = vb.viewRange()[1]
            self.label_item.setPos(sum(rgn) / 2, sum(yvb) / 2)

    def update_visible(self, visible):
        self.setVisible(visible)
        self.label_item.setVisible(visible)

    def update_bounds(self, bounds):
        self.setBounds(bounds)

    def remove(self):
        self.removeRequested.emit(self)
        vb = self.plot_widget.plotItem.vb
        if vb and self.label_item in vb.addedItems:
            vb.removeItem(self.label_item)

    def select(self, selected):
        self.selected = selected
        if selected:
            self.label_item.setColor("w")
            self.label_item.fill = pg.mkBrush(self.hover_color)
            self.gotSelected.emit(self)
        else:
            self.label_item.setColor(self.text_color)
            self.label_item.fill = pg.mkBrush(None)
        self.label_item.update()

    def mouseClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.movable:
            self.select(True)
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton and self.movable:
            self.remove()
            event.accept()
        else:
            event.ignore()

    def mouseDragEvent(self, event):
        if not self.movable or not event.button() == Qt.MouseButton.LeftButton:
            return
        event.accept()

        if event.isStart():
            bdp = event.buttonDownPos()
            self.cursorOffsets = [line.pos() - bdp for line in self.lines]
            self.startPositions = [line.pos() for line in self.lines]
            self.moving = True

        if not self.moving:
            return

        new_pos = [pos + event.pos() for pos in self.cursorOffsets]
        idx = 0 if new_pos[0].x() <= new_pos[1].x() else 1
        if new_pos[idx].x() < self.lines[idx].bounds()[0]:
            shift = self.lines[idx].bounds()[0] - new_pos[idx].x()
            for pos in new_pos:
                pos.setX(pos.x() + shift)
        if self.lines[(idx + 1) % 2].bounds()[1] < new_pos[(idx + 1) % 2].x():
            shift = (
                new_pos[(idx + 1) % 2].x()
                - self.lines[(idx + 1) % 2].bounds()[1]
            )
            for pos in new_pos:
                pos.setX(pos.x() - shift)

        with SignalBlocker(self.lines[0]):
            for pos, line in zip(new_pos, self.lines):
                line.setPos(pos)
        self.prepareGeometryChange()

        if event.isFinish():
            self.moving = False
            self.sigRegionChangeFinished.emit(self)
        else:
            self.sigRegionChanged.emit(self)


class ViewBox(pg.ViewBox):
    def __init__(self):
        super().__init__()
        self._drag_start = None
        self._drag_region = None
        self.plot_widget = None

    def set_plot_widget(self, widget):
        self.plot_widget = widget

    def mouseDragEvent(self, event):
        """Customize mouse drag events."""
        event.accept()
        if event.button() == Qt.MouseButton.LeftButton:
            if self.plot_widget.annotation_regions_requirements_satisfied():
                if event.isStart():
                    lv_labels = self.plot_widget.lv_labels
                    selected_indexes = lv_labels.selectedIndexes()
                    model = lv_labels.model()
                    label = LABEL_SEPARATOR.join(
                        [
                            model.data(index, Qt.ItemDataRole.DisplayRole)
                            for index in selected_indexes
                        ]
                    )
                    if len(selected_indexes) == 1:
                        label_color = model.data(
                            selected_indexes[0],
                            Qt.ItemDataRole.DecorationRole,
                        )
                        color = QColor(label_color)
                    else:
                        color = QColor()
                        for index in selected_indexes:
                            label_color = model.data(
                                index,
                                Qt.ItemDataRole.DecorationRole,
                            )
                            color.setRed(
                                color.red() // 2 + label_color.red() // 2
                            )
                            color.setGreen(
                                color.green() // 2 + label_color.green() // 2
                            )
                            color.setBlue(
                                color.blue() // 2 + label_color.blue() // 2
                            )
                    self._drag_start = self.mapSceneToView(
                        event.lastScenePos()
                    ).x()
                    self._drag_start = (
                        0 if self._drag_start < 0 else self._drag_start
                    )
                    drag_stop = self.mapSceneToView(event.scenePos()).x()
                    self._drag_region = AnnotationRegion(
                        plot_widget=self.plot_widget,
                        label=label,
                        color=color,
                        values=(self._drag_start, drag_stop),
                    )
                    self._drag_region.removeRequested.connect(
                        self.remove_region
                    )
                    self.sigYRangeChanged.connect(
                        self._drag_region.update_label_pos
                    )
                    self.plot_widget.annotation_regions.append(
                        self._drag_region
                    )
                elif event.isFinish():
                    drag_stop = self.mapSceneToView(event.scenePos()).x()
                    drag_stop = 0 if drag_stop < 0 else drag_stop
                    self._drag_region.setRegion((self._drag_start, drag_stop))
                    self._drag_region.select(True)
                    self._drag_region.setZValue(2)
                else:
                    x_to = self.mapSceneToView(event.scenePos()).x()
                    with SignalBlocker(self._drag_region):
                        self._drag_region.setRegion((self._drag_start, x_to))
        else:
            super().mouseDragEvent(event)

    def remove_region(self, region: AnnotationRegion):
        self.plot_widget.removeItem(region)
        self.plot_widget.removeItem(region.label_item)
        self.plot_widget.annotation_regions.remove(region)


class AnnotationPlotWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent, viewBox=ViewBox())
        self.plotItem.vb.set_plot_widget(self)
        self.annotation_regions = None
        self.lv_labels = None

    def set_annotation_regions_requirements(self, collection, lv_labels):
        self.annotation_regions = collection
        self.lv_labels = lv_labels

    def annotation_regions_requirements_satisfied(self):
        return (
            self.annotation_regions is not None
            and self.lv_labels is not None
            and len(self.lv_labels.selectedIndexes()) > 0
        )

    def update_annotation_regions_bounds(self, bounds):
        if self.annotation_regions is not None:
            for region in self.annotation_regions:
                region.update_bounds(bounds)
