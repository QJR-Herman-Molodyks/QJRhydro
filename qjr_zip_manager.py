from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QApplication, QMenuBar, QTextEdit
)
from PySide6.QtCore import Qt
import sys
import zipfile
import os

# ===================== COMPRESS =====================

class CompressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Compress")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Select data for compression into an archive:")
        layout.addWidget(self.label)

        self.btn_select_files = QPushButton("Select files")
        self.btn_select_folder = QPushButton("Select directory")
        self.btn_save_zip = QPushButton("Save ZIP")

        layout.addWidget(self.btn_select_files)
        layout.addWidget(self.btn_select_folder)
        layout.addWidget(self.btn_save_zip)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)

        # Data
        self.selected_paths = []

        # Signals
        self.btn_select_files.clicked.connect(self.select_files)
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_save_zip.clicked.connect(self.create_zip)

    def log_msg(self, text):
        self.log.append(text)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        if files:
            self.selected_paths = files
            self.log_msg(f"Selected files: {len(files)}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select directory")
        if folder:
            self.selected_paths = [folder]
            self.log_msg(f"Selected folder: {folder}")

    def create_zip(self):
        if not self.selected_paths:
            self.log_msg("No files selected!")
            return

        zip_path, _ = QFileDialog.getSaveFileName(self, "Save ZIP", "", "ZIP Files (*.zip)")
        if not zip_path:
            return

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for path in self.selected_paths:
                    if os.path.isfile(path):
                        zipf.write(path, os.path.basename(path))
                        self.log_msg(f"Added file: {path}")

                    elif os.path.isdir(path):
                        for root, dirs, files in os.walk(path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(full_path, path)
                                zipf.write(full_path, arcname)
                                self.log_msg(f"Added: {full_path}")

            self.log_msg("ZIP created successfully!!! Now you can close this window!")

        except Exception as e:
            self.log_msg(f"ERROR: {e}")


# ===================== UNCOMPRESS =====================

class UncompressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Extract ZIP Archive")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout()

        self.btn_select_zip = QPushButton("Select ZIP File")
        self.btn_select_dest = QPushButton("Select Destination Folder")
        self.btn_extract = QPushButton("Extract")

        layout.addWidget(self.btn_select_zip)
        layout.addWidget(self.btn_select_dest)
        layout.addWidget(self.btn_extract)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)

        # Data
        self.zip_file = None
        self.dest_folder = None

        # Signals
        self.btn_select_zip.clicked.connect(self.select_zip)
        self.btn_select_dest.clicked.connect(self.select_dest)
        self.btn_extract.clicked.connect(self.extract_zip)

    def log_msg(self, text):
        self.log.append(text)

    def select_zip(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select ZIP файл", "", "ZIP Files (*.zip)")
        if file:
            self.zip_file = file
            self.log_msg(f"ZIP вибрано: {file}")

    def select_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select a Destination Folder")
        if folder:
            self.dest_folder = folder
            self.log_msg(f"Destination folder selected: {folder}")

    def extract_zip(self):
        if not self.zip_file or not self.dest_folder:
            self.log_msg("Please select a ZIP file and a destination folder!")
            return

        try:
            with zipfile.ZipFile(self.zip_file, 'r') as zipf:
                zipf.extractall(self.dest_folder)
                self.log_msg("Extraction completed!!! You can now close this window!")

        except Exception as e:
            self.log_msg(f"ERROR: {e}")


# =============== MAIN =================

class QJRZipManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)


        self.setWindowTitle("QJR Zip Manager")
        self.setMinimumSize(560, 120)

        main_layout = QVBoxLayout()

        self.btn_compress = QPushButton("🗜️ Compress (Pack) Data into ZIP Archive")
        self.btn_compress.setFixedWidth(520)

        self.btn_uncompress = QPushButton("⬇️ Extract Data from ZIP Archive")
        self.btn_uncompress.setFixedWidth(520)

        main_layout.addWidget(self.btn_compress)
        main_layout.addWidget(self.btn_uncompress)

        self.setLayout(main_layout)

        # === Config ===

        self.zip_pack_path = None
        self.zip_pack_to_path = None
        self.zip_unpack_file_path = None
        self.zip_unpack_destination_path = None

        # === Signals ===

        self.btn_compress.clicked.connect(self.compress_data)
        self.btn_uncompress.clicked.connect(self.uncompress_data)

        # === Menu Bar ===

        self.menu_bar = QMenuBar()
        main_layout.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("File")


        file_menu.addAction("🗜️ Compress data to archive", self.compress_data)
        file_menu.addAction("⬇️ Extract data from archive", self.uncompress_data)
        file_menu.addSeparator()
        file_menu.addAction("⭕️ Exit", self.close)

    # === Styling (Experimental) for QJR magenta ===

        self.setStyleSheet("""
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

    # === Features ===

    def compress_data(self):
        dialog = CompressDialog(self)
        dialog.show()  # модальне вікно


    def uncompress_data(self):
        dialog = UncompressDialog(self)
        dialog.show()

def open_zip_manager(parent=None):
    dialog_zip_mgr = QJRZipManager(parent)
    dialog_zip_mgr.show()  # або show()
    return dialog_zip_mgr

# ===================== RUN =====================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QJRZipManager()
    window.show()

    sys.exit(app.exec())