import sys
import psutil
# import subprocess
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class StorageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Сховище")
        self.setMinimumSize(600, 400)
        self.setMaximumSize(1024, 768)
        self.setWindowIcon(QIcon("icons/drive.png"))  # якщо маєш іконку
        self.setModal(False)

        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel("Connected disks (drives)")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Device", "File System", "Used" ,"Size"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        # self.table.setIconSize(QSize(24, 24))  # або 32x32, 48x48
        self.table.setIconSize(QSize(24, 24))

        # Кнопки
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        close_btn = QPushButton("Close")

        refresh_btn.clicked.connect(self.load_disks)
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # Завантаження дисків при запуску
        self.load_disks()

    def load_disks(self):
        self.table.setRowCount(0)

        partitions = psutil.disk_partitions(all=True)

        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            # self.table.setItem(row, 0, QTableWidgetItem(part.device))
            item = QTableWidgetItem(QIcon("icons/storage_new.png"), part.device)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(part.fstype))

            total_gb = f"{usage.total / (1024**3):.1f} ГБ"
            used_gb = f"{usage.used / (1024**3):.1f} ГБ"

            self.table.setItem(row, 2, QTableWidgetItem(used_gb))
            self.table.setItem(row, 3, QTableWidgetItem(total_gb))

# --- 🔥 ОКРЕМА ФУНКЦІЯ ДЛЯ ВИКЛИКУ ДІАЛОГУ ---
def show_storage_dialog(parent=None):
    dlg_strg = StorageDialog(parent)
    dlg_strg.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                color: white;
                font-family: Consolas;
            }
            QPushButton {
                background: #2a2a2a;
                border: none;
                padding: 6px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #d1007a;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #444;
            }
            QSlider::handle:horizontal {
                background: #d1007a;
                width: 10px;
            }
        """)
    dlg_strg.show()     # модальний показ
    return dlg_strg     # можна повернути діалог, якщо треба щось зчитати


if __name__ == "__main__":
    app = QApplication(sys.argv)
    show_storage_dialog()
    sys.exit(app.exec())