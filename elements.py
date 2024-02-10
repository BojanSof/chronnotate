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

from utils import SignalBlocker


class ColorItemElement:
    __COLORS = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
        "#aec7e8",
        "#ffbb78",
        "#98df8a",
        "#ff9896",
        "#c5b0d5",
        "#c49c94",
        "#f7b6d2",
        "#c7c7c7",
        "#dbdb8d",
        "#9edae5",
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

    def __init__(self, plot_widget, label, values):
        super().__init__(
            values=values,
            orientation="vertical",
            movable=True,
            swapMode="sort",
            bounds=(0, 1000000),
        )
        self.setZValue(0)

        self.plot_widget = plot_widget
        self.sigRegionChangeFinished.connect(self.region_changed)
        self.label = label
        self.old_onset = values[0]
        self.selected = False

        self.label_item = pg.TextItem(text=label, anchor=(0.5, 0.5))
        # self.label_item.setFont(_q_font(10, bold=True))
        self.sigRegionChanged.connect(self.update_label_pos)

        self.update_color()
        self.plot_widget.addItem(self, ignoreBounds=True)
        self.plot_widget.addItem(self.label_item, ignoreBounds=True)

    def region_changed(self):
        self.regionChangeFinished.emit(self)
        self.update_label_pos()

    def update_color(self):
        # todo: get this colors from label settings
        self.base_color = QColor("#0FB3EF")
        self.hover_color = QColor("#0E9BCE")
        self.text_color = QColor("#0B7FA9")
        self.base_color.setAlpha(75)
        self.hover_color.setAlpha(150)
        self.text_color.setAlpha(255)
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

    def update_visible(self, visible):
        """Update if annotation-region is visible."""
        self.setVisible(visible)
        self.label_item.setVisible(visible)

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

    def mouseDragEvent(self, ev):
        if not self.movable or not ev.button() == Qt.MouseButton.LeftButton:
            return
        ev.accept()

        if ev.isStart():
            bdp = ev.buttonDownPos()
            self.cursorOffsets = [line.pos() - bdp for line in self.lines]
            self.startPositions = [line.pos() for line in self.lines]
            self.moving = True

        if not self.moving:
            return

        new_pos = [pos + ev.pos() for pos in self.cursorOffsets]
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

        if ev.isFinish():
            self.moving = False
            self.sigRegionChangeFinished.emit(self)
        else:
            self.sigRegionChanged.emit(self)

    def update_label_pos(self):
        rgn = self.getRegion()
        vb = self.plot_widget.plotItem.vb
        if vb:
            ymax = vb.viewRange()[1][1]
            self.label_item.setPos(sum(rgn) / 2, ymax - 0.3)


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
            if event.isStart():
                label = "Label"
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
                    values=(self._drag_start, drag_stop),
                )
            elif event.isFinish():
                drag_stop = self.mapSceneToView(event.scenePos()).x()
                drag_stop = 0 if drag_stop < 0 else drag_stop
                self._drag_region.setRegion((self._drag_start, drag_stop))
                # plot_onset = min(self._drag_start, drag_stop)
                # plot_offset = max(self._drag_start, drag_stop)
                # duration = abs(self._drag_start - drag_stop)

                self._drag_region.select(True)
                self._drag_region.setZValue(2)
            else:
                x_to = self.mapSceneToView(event.scenePos()).x()
                with SignalBlocker(self._drag_region):
                    self._drag_region.setRegion((self._drag_start, x_to))
                self._drag_region.update_label_pos()
        else:
            super().mouseDragEvent(event)

    # def mouseClickEvent(self, event):
    #     """Customize mouse click events."""
    #     # If we want the context-menu back, uncomment following line
    #     super().mouseClickEvent(event)
    #     if event.button() == Qt.MouseButton.LeftButton:
    #         print("Left click")
    #     elif event.button() == Qt.MouseButton.RightButton:
    #         print("Right click")


class AnnotationPlotWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent, viewBox=ViewBox())
        self.plotItem.vb.set_plot_widget(self)
