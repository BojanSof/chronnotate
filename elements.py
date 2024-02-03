import string

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant
from PyQt6.QtGui import QColor


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
            return QColor(item.color)

    def addItems(self):
        for key in self.modelDict:
            index = QModelIndex()
            self.beginInsertRows(index, 0, 0)
            self.items.append(key)
        self.endInsertRows()
