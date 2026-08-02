from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional, List

from PySide6.QtCore import Qt, QPoint, QRect, QSize
from PySide6.QtGui import (
    QAction,
    QColor,
    QFont,
    QImage,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPainterPathStroker,
)
from PySide6.QtWidgets import (
    QApplication,
    QColorDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


@dataclass
class Shape:
    kind: str
    color: QColor
    width: int = 2
    rect: Optional[QRect] = None
    path: Optional[QPainterPath] = None
    text: str = ""
    font: Optional[QFont] = None
    start: Optional[QPoint] = None
    end: Optional[QPoint] = None

    def translate(self, dx: int, dy: int) -> None:
        if self.rect:
            self.rect.translate(dx, dy)
        if self.path:
            self.path.translate(dx, dy)

    def contains(self, pos: QPoint) -> bool:
        # margin = 6
        margin = max(6, self.width)

        # 🖌️ Brush (path)
        if self.kind == "brush" and self.path:
            stroker = QPainterPathStroker()
            stroker.setWidth(self.width + margin)
            return stroker.createStroke(self.path).contains(pos)

        # 📏 Line (НОВЕ!)
        if self.kind == "line" and self.start and self.end:
            path = QPainterPath()
            path.moveTo(self.start)
            path.lineTo(self.end)

            stroker = QPainterPathStroker()
            stroker.setWidth(self.width + margin)
            return stroker.createStroke(path).contains(pos)

        # ⬛ Rect / Ellipse / Text
        if self.rect:
            return self.rect.adjusted(-margin, -margin, margin, margin).contains(pos)

        return False


class Canvas(QWidget):
    MODE_SELECT = "select"
    MODE_LINE = "line"
    MODE_RECT = "rect"
    MODE_ELLIPSE = "ellipse"
    MODE_TEXT = "text"
    MODE_BRUSH = "brush"
    MODE_ERASER = "eraser"

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(900, 600)
        self.setMouseTracking(True)

        self.mode = self.MODE_SELECT
        self.pen_color = QColor("white")
        self.pen_width = 2
        self.text_value = "Text"
        self.grid_enabled = True

        self.shapes: List[Shape] = []
        self.selected: Optional[Shape] = None

        self.start = QPoint()
        self.end = QPoint()
        self.preview_path: Optional[QPainterPath] = None
        self.drawing = False
        self.dragging = False
        self.last_mouse = QPoint()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.drawing = False
        self.dragging = False
        self.preview_path = None
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        pos = event.pos()
        self.last_mouse = pos

        if self.mode == self.MODE_SELECT:
            self.selected = None
            for shape in reversed(self.shapes):
                if shape.contains(pos):
                    self.selected = shape
                    self.dragging = True
                    break
            self.update()
            return

        if self.mode == self.MODE_TEXT:
            font = QFont("Consolas", 16)
            rect = QRect(pos, QSize(220, 30))
            self.shapes.append(Shape("text", self.pen_color, self.pen_width, rect, text=self.text_value, font=font))
            self.update()
            return

        self.start = pos
        self.end = pos
        self.drawing = True

        if self.mode == self.MODE_BRUSH:
            self.preview_path = QPainterPath()
            self.preview_path.moveTo(pos)

        self.preview_path = None

        if self.mode in (self.MODE_BRUSH, self.MODE_ERASER):
            self.preview_path = QPainterPath()
            self.preview_path.moveTo(pos)

    def mouseMoveEvent(self, event):
        pos = event.pos()

        if self.dragging and self.selected and (event.buttons() & Qt.LeftButton):
            dx = pos.x() - self.last_mouse.x()
            dy = pos.y() - self.last_mouse.y()
            self.selected.translate(dx, dy)
            self.last_mouse = pos
            self.update()
            return

        if not self.drawing or not (event.buttons() & Qt.LeftButton):
            return

        self.end = pos
        if self.preview_path is not None:
            self.preview_path.lineTo(pos)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        if self.dragging:
            self.dragging = False
            return

        if not self.drawing:
            return

        self.drawing = False
        rect = QRect(self.start, self.end).normalized()

        # if self.mode == self.MODE_LINE:
        #     self.shapes.append(Shape("line", self.pen_color, self.pen_width, rect))
        if self.mode == self.MODE_LINE:
            self.shapes.append(
            Shape("line", self.pen_color, self.pen_width, start=self.start, end=self.end)
        )
        elif self.mode == self.MODE_RECT:
            self.shapes.append(Shape("rect", self.pen_color, self.pen_width, rect))
        elif self.mode == self.MODE_ELLIPSE:
            self.shapes.append(Shape("ellipse", self.pen_color, self.pen_width, rect))
        elif self.mode == self.MODE_BRUSH and self.preview_path:
            self.shapes.append(Shape("brush", self.pen_color, self.pen_width, path=self.preview_path))
        elif self.mode == self.MODE_ERASER and self.preview_path:
            self._erase_with_path(self.preview_path)

        self.preview_path = None
        self.update()

    def _erase_at_point(self, pos: QPoint):
        self.shapes = [
            shape for shape in self.shapes
            if not shape.contains(pos)
        ]

        if self.selected and not self.selected.contains(pos):
            return

        self.selected = None

    def _erase_with_path(self, eraser_path: QPainterPath):
        new_shapes = []

        for shape in self.shapes:
            if shape.kind == "brush" and shape.path:
                stroker = QPainterPathStroker()
                stroker.setWidth(shape.width + 4)
                stroke = stroker.createStroke(shape.path)

                if not eraser_path.intersects(stroke):
                    new_shapes.append(shape)

            elif shape.rect:
                if not eraser_path.boundingRect().intersects(shape.rect):
                    new_shapes.append(shape)
            else:
                new_shapes.append(shape)

        self.shapes = new_shapes

        if self.selected and self.selected not in self.shapes:
            self.selected = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.selected:
            if self.selected in self.shapes:
                self.shapes.remove(self.selected)
                self.selected = None
                self.update()

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.black)

        if self.grid_enabled:
            self._draw_grid(painter)

        for shape in self.shapes:
            self._draw_shape(painter, shape)

        if self.preview_path:
            painter.setPen(QPen(self.pen_color, self.pen_width))
            painter.drawPath(self.preview_path)

        elif self.drawing:
            if self.mode == self.MODE_LINE:
                painter.setPen(QPen(self.pen_color, self.pen_width, Qt.DashLine))
                painter.drawLine(self.start, self.end)

            elif self.mode in (self.MODE_RECT, self.MODE_ELLIPSE):
                preview = Shape(
                    self.mode,
                    self.pen_color,
                    self.pen_width,
                    QRect(self.start, self.end).normalized()
                )
                self._draw_shape(painter, preview, preview_mode=True)

            else:
                rect = QRect(self.start, self.end).normalized()
                preview = Shape(self.mode, self.pen_color, self.pen_width, rect)
                self._draw_shape(painter, preview, preview_mode=True)

        if self.preview_path:
            if self.mode == self.MODE_ERASER:
                # 👇 інший стиль для гумки
                pen = QPen(QColor(0, 200, 255, 180), self.pen_width * 2)
                pen.setStyle(Qt.DashLine)  # пунктир
                painter.setPen(pen)
            else:
                painter.setPen(QPen(self.pen_color, self.pen_width))

            painter.drawPath(self.preview_path)

    def _draw_grid(self, painter: QPainter):
        painter.setPen(QPen(QColor(45, 45, 45), 1))
        step = 25
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)

    def _draw_shape(self, painter: QPainter, shape: Shape, preview_mode: bool = False):
        pen_style = Qt.DashLine if preview_mode else Qt.SolidLine
        painter.setPen(QPen(shape.color, shape.width, pen_style))

        if shape.kind == "line" and shape.start and shape.end:
            painter.drawLine(shape.start, shape.end)
        elif shape.kind == "rect" and shape.rect:
            painter.drawRect(shape.rect)
        elif shape.kind == "ellipse" and shape.rect:
            painter.drawEllipse(shape.rect)
        elif shape.kind == "text" and shape.rect:
            painter.setFont(shape.font or QFont("Consolas", 16))
            painter.drawText(shape.rect.topLeft(), shape.text)

        elif shape.kind == "brush" and shape.path:
            if shape.color == QColor("transparent"):
                painter.setCompositionMode(QPainter.CompositionMode_Clear)
                painter.setPen(QPen(Qt.transparent, shape.width))
                painter.drawPath(shape.path)
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            else:
                painter.drawPath(shape.path)


    def clear(self):
        self.shapes.clear()
        self.selected = None
        self.update()

    def undo(self):
        if self.shapes:
            self.shapes.pop()
            self.selected = None
            self.update()

    def export_png(self, path: str):
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        pixmap.save(path)

    def contains(self, pos: QPoint) -> bool:
        if self.kind == "brush" and self.path:
            stroker = QPainterPathStroker()
            stroker.setWidth(self.width + 8)
            return stroker.createStroke(self.path).contains(pos)

        if self.rect:
            return self.rect.adjusted(-6, -6, 6, 6).contains(pos)

        return False


class DrawingEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QJR Editor of graphics and diagrams")
        self.resize(1200, 800)

        central = QWidget()
        root = QVBoxLayout(central)
        toolbar = QHBoxLayout()

        self.canvas = Canvas()

        def add_btn(title: str, callback):
            btn = QPushButton(title)
            btn.clicked.connect(callback)
            toolbar.addWidget(btn)
            return btn

        add_btn("Select", lambda: self.canvas.set_mode(Canvas.MODE_SELECT))
        add_btn("Line", lambda: self.canvas.set_mode(Canvas.MODE_LINE))
        add_btn("Rectangle", lambda: self.canvas.set_mode(Canvas.MODE_RECT))
        add_btn("Ellipse", lambda: self.canvas.set_mode(Canvas.MODE_ELLIPSE))
        add_btn("Brush", lambda: self.canvas.set_mode(Canvas.MODE_BRUSH))
        add_btn("Eraser", lambda: self.canvas.set_mode(Canvas.MODE_ERASER))
        add_btn("Text", self.set_text)
        add_btn("Color", self.pick_color)
        add_btn("Undo", self.canvas.undo)
        add_btn("Clear", self.canvas.clear)
        add_btn("Exit", self.close)
        add_btn("Export PNG", self.export_png)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(20)
        self.slider.setValue(2)
        self.slider.valueChanged.connect(self.set_pen_width)
        toolbar.addWidget(self.slider)

        root.addLayout(toolbar)
        root.addWidget(self.canvas)
        self.setCentralWidget(central)

        clear_action = QAction("Clear", self)
        clear_action.setShortcut(QKeySequence("Ctrl+L"))
        clear_action.triggered.connect(self.canvas.clear)
        self.addAction(clear_action)

    def set_pen_width(self, value: int):
        self.canvas.pen_width = value

    def pick_color(self):
        color = QColorDialog.getColor(self.canvas.pen_color, self)
        if color.isValid():
            self.canvas.pen_color = color

    def set_text(self):
        text, ok = QInputDialog.getText(self, "Text", "Enter text")
        if ok and text:
            self.canvas.text_value = text
            self.canvas.set_mode(Canvas.MODE_TEXT)

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG", "diagram.png", "PNG Files (*.png)")
        if path:
            self.canvas.export_png(path)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Exit",
            "Close QJR Diagrams?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

def create_diagrams_graphics(parent=None):
    """Backward-compatible factory function for legacy Q-J-R launcher."""
    window = DrawingEditor()
    if parent is not None:
        window.setParent(parent)
    return window

def main():
    app = QApplication([])
    window = DrawingEditor()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()