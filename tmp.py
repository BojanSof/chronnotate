import sys

import pyqtgraph as pg
from PyQt6 import QtCore, QtWidgets


class AnnotationRegion(pg.LinearRegionItem):
    def __init__(self, start_pos):
        super().__init__([start_pos.x(), start_pos.x()])
        self.start_pos = start_pos

    def updateRegion(self, end_pos):
        self.setRegion([self.start_pos.x(), end_pos.x()])

    def containsPoint(self, x, y):
        return self.boundingRect().contains(x, y)


class AnnotationApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Annotation App")

        # Create a PlotWidget
        self.plotWidget = pg.PlotWidget()
        self.setCentralWidget(self.plotWidget)

        # Initialize start point for the annotation
        self.start_point = None
        self.current_region = None
        self.selected_region = None

        # Install event filter on the plot widget
        self.plotWidget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.plotWidget:
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                self.onMousePressed(event)
                return True
            elif event.type() == QtCore.QEvent.Type.MouseMove:
                self.onMouseMoved(event)
                return True
            elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
                self.onMouseReleased(event)
                return True
        return super().eventFilter(obj, event)

    def onMousePressed(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Get mouse click position in plot coordinates
            pos = event.pos().toPointF()
            mouse_pos = self.plotWidget.plotItem.mapFromScene(pos)

            # Check if mouse click is near the edge of an existing region
            for item in self.plotWidget.items():
                if isinstance(item, AnnotationRegion):
                    if item.containsPoint(mouse_pos.x(), mouse_pos.y()):
                        self.selected_region = item
                        return

            # If not near an existing region, start a new annotation
            self.start_point = self.plotWidget.plotItem.vb.mapSceneToView(pos)
            self.current_region = AnnotationRegion(self.start_point)
            self.plotWidget.addItem(self.current_region)

    def onMouseMoved(self, event):
        if (
            self.selected_region is not None
            and self.selected_region is not None
        ):
            # Get mouse position while moving
            pos = event.pos()
            current_point = self.plotWidget.plotItem.mapFromScene(pos)

            # Update the selected region
            self.selected_region.updateRegion(current_point)

    def onMouseReleased(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.selected_region is not None:
                self.selected_region = None
            elif self.current_region is not None:
                # Reset points
                self.start_point = None
                self.current_region = None

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Delete:
            # Remove the last added annotation region
            for item in self.plotWidget.items():
                if isinstance(item, AnnotationRegion):
                    self.plotWidget.removeItem(item)
                    break


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AnnotationApp()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
