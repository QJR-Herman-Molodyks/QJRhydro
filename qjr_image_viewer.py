import os

from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QScrollArea,
    QHBoxLayout, QPushButton, QMenuBar, QFileDialog
)
from PySide6.QtGui import QPixmap, QTransform, QAction, QKeySequence
from PySide6.QtCore import Qt, QEvent

class ImageViewer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("QJR Image Viewer")
        self.resize(800, 600)

        self.pixmap = None
        self.zoom = 1.0

        self.image_list = []
        self.current_index = -1

        layout = QVBoxLayout(self)

        # ===== Menu Bar =====

        self.menu_bar = QMenuBar()
        layout.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("File")

        open_action = QAction("⬇️ Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_image)

        exit_action = QAction("⭕️ Close", self)
        exit_action.setShortcut(QKeySequence.Close)
        exit_action.triggered.connect(self.close)
        
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # ===== Toolbar =====
        toolbar = QHBoxLayout()

        self.btn_prev = QPushButton("< Previous")
        self.btn_next = QPushButton("Next >")

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out = QPushButton("-")

        self.btn_fit = QPushButton("Fit")
        self.btn_actual = QPushButton("100%")
        self.btn_half = QPushButton("50%")

        self.btn_rotate_l = QPushButton("⟲")
        self.btn_rotate_r = QPushButton("⟳")

        toolbar.addWidget(self.btn_prev)
        toolbar.addWidget(self.btn_next)

        toolbar.addSpacing(20)

        toolbar.addWidget(self.btn_zoom_in)
        toolbar.addWidget(self.btn_zoom_out)

        toolbar.addWidget(self.btn_fit)
        toolbar.addWidget(self.btn_actual)
        toolbar.addWidget(self.btn_half)

        toolbar.addSpacing(20)

        toolbar.addWidget(self.btn_rotate_l)
        toolbar.addWidget(self.btn_rotate_r)

        toolbar.addStretch()

        layout.addLayout(toolbar)

        # ===== Image area =====
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        self.scroll.setWidget(self.label)
        layout.addWidget(self.scroll)

        # wheel zoom
        self.scroll.viewport().installEventFilter(self)

        # ===== Signals =====
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)

        self.btn_fit.clicked.connect(self.fit_image)
        self.btn_actual.clicked.connect(self.actual_size)
        self.btn_half.clicked.connect(self.half_size)

        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next.clicked.connect(self.next_image)

        self.btn_rotate_l.clicked.connect(self.rotate_left)
        self.btn_rotate_r.clicked.connect(self.rotate_right)

    # ===== Load image =====

    def load_image(self, path):

        path = os.path.normpath(path)

        folder = os.path.dirname(path)

        extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")

        # будуємо список лише один раз
        self.image_list = [
            os.path.normpath(os.path.join(folder, f))
            for f in os.listdir(folder)
            if f.lower().endswith(extensions)
        ]

        self.image_list.sort(key=str.lower)

        if path in self.image_list:
            self.current_index = self.image_list.index(path)
        else:
            self.image_list.append(path)
            self.current_index = len(self.image_list) - 1

        self.load_current_image()

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open",
            "",
            "Світлини (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;PNG Світлина (*.png);;JPG Image (*.jpg);;SVG Світлина (*.svg);;BMP Світлина (*.bmp);;GIF світлина (*.gif);;WEBP світлина (*.webp);;Всі файли (*)"
        )

        if not path:
            return

        self.load_image(path)

    def load_current_image(self):

        if not self.image_list:
            return

        path = self.image_list[self.current_index]

        self.pixmap = QPixmap(path)

        if self.pixmap.isNull():
            return

        self.fit_image()

    #Rendering
    def update_image(self):

        if not self.pixmap:
            return

        size = self.pixmap.size() * self.zoom

        scaled = self.pixmap.scaled(
            size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.label.setPixmap(scaled)

    # ==== Zoom =====
    def zoom_in(self):
        self.zoom *= 1.25
        self.zoom = max(0.05, min(self.zoom, 20))
        self.update_image()

    def zoom_out(self):
        self.zoom *= 0.8
        self.zoom = max(0.05, min(self.zoom, 20))
        self.update_image()

    #  Fit
    def fit_image(self):

        if not self.pixmap:
            return

        area = self.scroll.viewport().size()
        img = self.pixmap.size()

        scale_w = area.width() / img.width()
        scale_h = area.height() / img.height()

        self.zoom = min(scale_w, scale_h)

        self.update_image()

    # actual size zooming
    def actual_size(self):
        self.zoom = 1.0
        self.update_image()

    # half size zoom
    def half_size(self):
        self.zoom = 0.5
        self.update_image()

    # rotation
    def rotate_left(self):
        if not self.pixmap:
            return

        transform = QTransform().rotate(-90)
        self.pixmap = self.pixmap.transformed(transform)

        self.update_image()

    def rotate_right(self):
        if not self.pixmap:
            return

        transform = QTransform().rotate(90)
        self.pixmap = self.pixmap.transformed(transform)

        self.update_image()

    def next_image(self):
        if not self.image_list:
            return

        self.current_index = (self.current_index + 1) % len(self.image_list)

        self.load_current_image()

    def prev_image(self):
        if not self.image_list:
            return

        self.current_index = (self.current_index - 1) % len(self.image_list)
        self.load_current_image()

    # ===== Wheel zoom =====
    def eventFilter(self, obj, event):
        if obj == self.scroll.viewport() and event.type() == QEvent.Wheel:
            modifiers = event.modifiers()

            if modifiers & (Qt.ControlModifier | Qt.MetaModifier):
                if event.angleDelta().y() > 0:
                    self.zoom *= 1.15
                else:
                    self.zoom *= 0.85

                self.zoom = max(0.05, min(self.zoom, 20))
                self.update_image()
                return True

        return super().eventFilter(obj, event)

    # ====== Key press event

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Right:
            self.next_image()

        elif event.key() == Qt.Key_Left:
            self.prev_image()


def create_image_viewer(parent=None, file_path=None):
    viewer = ImageViewer(parent)

    if file_path:
        viewer.load_image(file_path)

    return viewer