from PySide6.QtWidgets import (
    QDialog, QTreeView, QListView, QFileIconProvider, QFileSystemModel,
    QSplitter, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QMenu, QMessageBox, QInputDialog, QHeaderView
)
from PySide6.QtCore import Qt, QDir, QSize
from PySide6.QtGui import (
    QDesktopServices,
    QIcon,
    QShortcut,
    QKeySequence,
    QStandardItemModel,
    QStandardItem
)
from PySide6.QtCore import QUrl, QFileInfo

import os
import shutil
import json

from datetime import datetime

from qjr_image_viewer import *
from qjr_zip_manager import *
from fsSecurityMgrService import *

# 🔴 ГЛОБАЛЬНЕ ПОСИЛАННЯ
_file_manager_instance = None

image_ext = ["png", "jpg", "jpeg", "bmp", "gif", "webp"]
text_ext = ["txt", "qjr", "json", "csv", "py", "cpp", "cxx", "c", "h", "asm", "log", "xml", "yaml", "yml", "toml",
            "plist", "sh"]
music_ext = ["wav", "ogg", "aiff", "flac"]
video_ext = ["mp4", "avi", "mkv", "mov", "wmv"]

class CustomIconProvider(QFileIconProvider):

    def icon(self, file_info):

        if file_info.isDir():
            return QIcon("icons/folder.png")

        suffix = file_info.suffix().lower()

        if suffix in image_ext:
            return QIcon("icons/image.png")

        if suffix in text_ext:
            return QIcon("icons/text_file.png")

        if suffix in music_ext:
            return QIcon("icons/music_file.png")

        if suffix == "mp3":
            return QIcon("icons/file_music_mp3.png")

        if suffix in video_ext:
            return QIcon("icons/video.png")

        return QIcon("icons/file.png")


class FileManagerDialog(QDialog):
    def __init__(self, parent=None, path=None):
        super().__init__(parent)

        self.clipboard_path = None
        self.cut_mode = False

        self.setWindowTitle("QJR File Manager")
        self.resize(1100, 750)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.history = []

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.favorites_file = os.path.join(self.base_dir, "favorites.json")
        self.settings_file = os.path.join(self.base_dir, "user_settings.json")
        self.hidden_files_file = os.path.join(self.base_dir, "hiddenFiles.qjr")
        self.favorites = []

        # === Layout ===

        layout = QVBoxLayout(self)

        # === Навігація ===
        nav = QHBoxLayout()
        self.btn_back = QPushButton("<--")
        self.btn_up = QPushButton("..")
        self.path_edit = QLineEdit()
        # self.path_edit.setReadOnly(True)
        self.btn_go = QPushButton("Go ->")
        self.btn_external = QPushButton("Open Externally")

        nav.addWidget(self.btn_external)
        nav.addWidget(self.btn_back)
        nav.addWidget(self.btn_up)
        nav.addWidget(self.path_edit)
        nav.addWidget(self.btn_go)
        layout.addLayout(nav)

        # === Splitter ===
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        self.model = QFileSystemModel(self)
        self.model.setIconProvider(CustomIconProvider())
        # self.model.setRootPath(QDir.rootPath())
        self.model.setRootPath("")
        self.apply_hidden_files_setting()


        # TREE

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree.setHeaderHidden(True)
        self.tree.setRootIndex(self.model.index(""))
        self.tree.clicked.connect(self.on_tree_clicked)

        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setStretchLastSection(True)

        # LIST

        self.list = QListView()
        self.list.setModel(self.model)
        self.list.doubleClicked.connect(self.on_list_double_clicked)

        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.open_context_menu)

        self.list.setViewMode(QListView.ListMode)
        self.apply_list_view(32)
        self.list.setUniformItemSizes(True)

        # Settings

        self.settings = self.load_settings()
        self.apply_settings()

        # === FS init unit ===
        # self.root_path = get_user_fs()
        self.root_path = path if path else get_user_fs()

        # List стартує в user
        self.set_path(self.root_path)

        # Розкрити дерево до user
        index = self.model.index(self.root_path)

        parent = index
        while parent.isValid():
            self.tree.expand(parent)
            parent = parent.parent()

        # === FAVORITES PANEL ===
        # self.fav_list = QListView()
        # self.fav_model = QFileSystemModel()s

        self.fav_tree = QTreeView()
        self.fav_tree.setHeaderHidden(True)
        self.fav_tree.setEditTriggers(QTreeView.NoEditTriggers)
        self.fav_tree.doubleClicked.connect(self.open_favorite)

        self.fav_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fav_tree.customContextMenuRequested.connect(
            self.favorites_context_menu
        )

        # self.fav_list.setEditTriggers(QListView.NoEditTriggers)
        #
        # self.fav_list.doubleClicked.connect(self.open_favorite)
        # self.fav_list.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.fav_list.customContextMenuRequested.connect(self.favorites_context_menu)
        #
        # splitter.addWidget(self.fav_list)
        splitter.addWidget(self.fav_tree)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.list)

        # === Part of a favorites panel ===

        self.load_favorites()

        # === Navigation buttons ===

        self.btn_back.clicked.connect(self.go_back)
        self.btn_up.clicked.connect(self.go_up)
        self.btn_external.clicked.connect(self.open_external)

        self.btn_go.clicked.connect(self.on_go_clicked)
        self.path_edit.returnPressed.connect(self.on_go_clicked)

    # ---------- Навігація ----------
    # def set_path(self, path):
    #     index = self.model.index(path)
    #     if not index.isValid():
    #         return
    #
    #     current = self.path_edit.text()
    #     if current and current != path:
    #         self.history.append(current)
    #
    #     self.tree.setCurrentIndex(index)
    #     self.list.setRootIndex(index)
    #     self.path_edit.setText(path)
    # python
    def set_path(self, path):
        # Ensure model knows about the requested drive/root (important on Windows)
        index = self.model.index(path)
        if not index.isValid():
            drive, _ = os.path.splitdrive(path)
            if drive:
                root = drive + os.sep
                self.model.setRootPath(root)
                self.tree.setRootIndex(self.model.index(root))
                index = self.model.index(path)
                if not index.isValid():
                    return
            else:
                return
        else:
            # If model's current root is on a different drive, switch it (Windows)
            model_root = self.model.rootPath()
            drive_new = os.path.splitdrive(path)[0]
            drive_current = os.path.splitdrive(model_root)[0]
            if drive_new and drive_new != drive_current:
                root = drive_new + os.sep
                self.model.setRootPath(root)
                self.tree.setRootIndex(self.model.index(root))

        # history
        current = self.path_edit.text()
        if current and current != path:
            self.history.append(current)

        # update views
        self.tree.setCurrentIndex(index)
        self.list.setRootIndex(index)
        self.path_edit.setText(path)

        # expand tree down to the selected index
        parent = index
        while parent.isValid():
            self.tree.expand(parent)
            parent = parent.parent()

    def go_back(self):
        if self.history:
            self.set_path(self.history.pop())

    def go_up(self):
        d = QDir(self.path_edit.text())
        if d.cdUp():
            self.set_path(d.absolutePath())

    # def on_tree_clicked(self, index):
    #     self.set_path(self.model.filePath(index))
    def on_tree_clicked(self, index):
        path = self.model.filePath(index)
        self.set_path(path)
        self.open_with_qjr(path)

    def paste_selected(self):

        dest = os.path.join(
            self.path_edit.text(),
            os.path.basename(self.clipboard_path)
        )

        try:
            if os.path.isdir(self.clipboard_path):
                if self.cut_mode:
                    shutil.move(self.clipboard_path, dest)
                else:
                    shutil.copytree(self.clipboard_path, dest)
            else:
                if self.cut_mode:
                    shutil.move(self.clipboard_path, dest)
                else:
                    shutil.copy2(self.clipboard_path, dest)

            if self.cut_mode:
                self.clipboard_path = None
                self.cut_mode = False

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def apply_list_view(self, icon_size):
        self.list.setViewMode(QListView.ListMode)
        self.list.setGridSize(QSize(40, 40))
        self.list.setIconSize(QSize(icon_size, icon_size))

    def apply_icon_view(self):
        self.list.setViewMode(QListView.IconMode)
        self.list.setGridSize(QSize(90, 90))
        self.list.setResizeMode(QListView.Adjust)
        self.list.setIconSize(QSize(64, 64))

    def create_file(self):
        name, ok = QInputDialog.getText(self, "New File", "File Name:")

        if ok and name:
            path = os.path.join(self.path_edit.text(), name)
            if os.path.exists(path):
                QMessageBox.warning(self, "Error", f"File {name} is already exists")
            else:
                with open(path, "w") as f:
                    pass

    def create_folder(self):

        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")

        if ok and name:
            path = os.path.join(self.path_edit.text(), name)
            os.makedirs(path, exist_ok=True)

    def delete_file(self, index):

        path = self.model.filePath(index)

        reply = QMessageBox.question(
            self,
            "Delete",
            "Delete this file?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:

            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    def rename_file(self, index):

        path = self.model.filePath(index)
        old_name = os.path.basename(path)

        name, ok = QInputDialog.getText(
            self,
            "Rename",
            "New name:",
            text=old_name
        )

        if ok and name:
            new_path = os.path.join(os.path.dirname(path), name)
            os.rename(path, new_path)

    # python
    def on_go_clicked(self):
        raw = self.path_edit.text().strip()
        if not raw:
            return

        # Expand ~ and environment variables, make absolute
        path = os.path.expanduser(os.path.expandvars(raw))
        path = os.path.abspath(path)

        if not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"Path does not exist:\n{path}")
            return

        if os.path.isdir(path):
            # Direct directory -> navigate into it
            self.set_path(path)
        else:
            # If it's a file, navigate to its folder and try to select it
            dirpath = os.path.dirname(path)
            self.set_path(dirpath)

            idx = self.model.index(path)
            if idx.isValid():
                # select in list and tree so user sees the file
                self.list.setCurrentIndex(idx)
                self.tree.setCurrentIndex(idx)

    def show_properties(self, path):
        info = QFileInfo(path)

        name = info.fileName()
        location = info.absoluteFilePath()
        size = info.size()
        modified = info.lastModified().toString()

        type_file = "Folder" if info.isDir() else "File"

        # translate labels
        type_label = "Folder" if info.isDir() else "File"
        text = (
            f"Name: {name}\n"
            f"Type: {type_label}\n"
            f"Size: {size} bytes\n"
            f"Modified: {modified}\n\n"
            f"Path:\n{location}"
        )

        QMessageBox.information(self, "Properties", text)

    def open_with_notepad(self, path):
        from qjr_notepad import create_notepad

        editor = create_notepad(self)
        editor.load_file(path)
        editor.show()

    def open_with_image_viewer(self, path):
        from qjr_image_viewer import create_image_viewer

        viewer = create_image_viewer(self, path)
        viewer.show()

    def open_with_media_player(self, path):
        from qjr_media_player import create_player

        player = create_player(self)
        player.load_file(path)  # або будь-який шлях
        player.show()

    def open_context_menu(self, pos):
        index = self.list.indexAt(pos)
        path = self.model.filePath(index)

        menu = QMenu(self)

        open_file = menu.addAction("➡️ Open")
        add_fav = menu.addAction("⭐️ Add to Favorites")

        menu.addSeparator()

        new_file = menu.addAction("📄 New File")
        new_folder = menu.addAction("📁 New Folder")

        if index.isValid():
            menu.addSeparator()
            rename = menu.addAction("✏️ Rename")
            delete = menu.addAction("🗑️ Delete")
            menu.addSeparator()
            copy_action = menu.addAction("📑 Copy")
            cut_action = menu.addAction("✂️ Cut")

        menu.addSeparator()
        paste_action = menu.addAction("📋 Paste")

        menu.addSeparator()

        if os.path.isfile(path):

            cant_be_opened_with_other_apps = False

            open_with_menu = None
            open_with_notepad = None
            open_with_image_viewer = None
            open_with_media_player = None
            open_with_video_player = None
            open_with_zip_manager = None

            if index.isValid() and not self.model.isDir(index):
                menu.addSeparator()

                open_with_menu = menu.addMenu("🗂️ Open with")

                open_with_notepad = open_with_menu.addAction("📝 QJR Notepad")

                open_with_image_viewer = open_with_menu.addAction("🌠 QJR Image Viewer")

                open_with_media_player = open_with_menu.addAction("▶️ QJR Media Player")

                open_with_video_player = open_with_menu.addAction("🎥 QJR Video Player")

                open_with_zip_manager = open_with_menu.addAction("🗜️ QJR ZIP Manager")

            menu.addSeparator()

        else:
            cant_be_opened_with_other_apps = True

        sort_name = menu.addAction("🏷️ Sort by name")
        sort_date = menu.addAction("📆 Sort by date")
        sort_type = menu.addAction("🗳️ Sort by type")

        menu.addSeparator()

        # Create new:

        create_new = menu.addMenu("+ Create")

        create_new_folder = create_new.addAction("📁 Folder")
        create_new_file = create_new.addAction("📄 File")

        create_new.addSeparator()

        create_new_text_file = create_new.addAction("📄 Text File")
        create_new_python_file = create_new.addAction("🐍 Python File")
        create_new_qjr_file = create_new.addAction("😀 Q-J-R File")
        create_new_json_file = create_new.addAction("⚒️ JSON File")
        create_new_csv_file = create_new.addAction("↔️ CSV File")
        create_new_xml_file = create_new.addAction("🔀 XML File")
        create_new_yml_file = create_new.addAction("*️⃣ YML File")
        create_new_yaml_file = create_new.addAction("↕️ YAML File")

        menu.addSeparator()

        toggle_files_view = menu.addAction("😶‍🌫️ Hide/Show Hidden files")

        menu.addSeparator()

        view_icons = menu.addAction("🔲 View: Icons")
        view_list = menu.addAction("🔖 View: List")

        menu.addSeparator()

        properties_action = menu.addAction("ℹ️ Properties")
        properties_action.triggered.connect(lambda: self.show_properties(path))

        action = menu.exec(self.list.viewport().mapToGlobal(pos))

        if action == new_file or action == create_new_file:
            self.create_file()

        elif action == new_folder or action == create_new_folder:
            self.create_folder()

        elif index.isValid() and action == rename:
            self.rename_file(index)

        elif index.isValid() and action == delete:
            self.delete_file(index)

        elif action == sort_name:
            # self.list.sortByColumn(0, Qt.AscendingOrder)
            self.model.sort(0, Qt.AscendingOrder)

        elif action == sort_date:
            # self.list.sortByColumn(3, Qt.DescendingOrder)
            self.model.sort(3, Qt.DescendingOrder)

        elif action == sort_type:
            self.model.sort(1, Qt.AscendingOrder)

        elif action == view_icons:
            self.apply_icon_view()

        elif action == view_list:
            self.apply_list_view(32)

        elif action == open_file:
            if self.model.isDir(index):
                self.set_path(self.model.filePath(index))
            else:
                self.open_internal(index)

        elif action == add_fav:
            if path not in self.favorites:
                self.favorites.append(path)
                self.save_favorites()
                self.update_favorites_view()

        elif index.isValid() and action == copy_action:
            self.clipboard_path = path
            self.cut_mode = False

        elif index.isValid() and action == cut_action:
            self.clipboard_path = path
            self.cut_mode = True

        elif action == toggle_files_view:
            self.toggle_files_view()

        elif action == paste_action:
            if self.clipboard_path and os.path.exists(self.clipboard_path):

                dest = os.path.join(
                    self.path_edit.text(),
                    os.path.basename(self.clipboard_path)
                )

                try:
                    if os.path.isdir(self.clipboard_path):
                        if self.cut_mode:
                            shutil.move(self.clipboard_path, dest)
                        else:
                            shutil.copytree(self.clipboard_path, dest)
                    else:
                        if self.cut_mode:
                            shutil.move(self.clipboard_path, dest)
                        else:
                            shutil.copy2(self.clipboard_path, dest)

                    if self.cut_mode:
                        self.clipboard_path = None
                        self.cut_mode = False

                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))


        # === Create a specific file ===

        elif action == create_new_text_file:
            self.create_file_with_ext("txt")

        elif action == create_new_python_file:
            self.create_file_with_ext("py")

        elif action == create_new_qjr_file:
            self.create_file_with_ext("qjr")

        elif action == create_new_json_file:
            self.create_file_with_ext("json")

        elif action == create_new_csv_file:
            self.create_file_with_ext("csv")

        elif action == create_new_xml_file:
            self.create_file_with_ext("xml")

        elif action == create_new_yml_file:
            self.create_file_with_ext("yml")

        elif action == create_new_yaml_file:
            self.create_file_with_ext("yaml")


        # === Other ===

        elif cant_be_opened_with_other_apps == True:
            pass

        else:
            if action == open_with_notepad:
                self.open_with_notepad(path)

            elif action == open_with_image_viewer:
                self.open_with_image_viewer(path)

            elif action == open_with_media_player:
                self.open_with_media_player(path)

            elif action == open_with_video_player:
                # Ensure the video player action actually opens the player
                self.open_with_video_player(path)

            elif action == open_with_zip_manager:
                self.open_with_zip_manager(path)

    def open_internal(self, index):

        path = self.model.filePath(index)
        ext = os.path.splitext(path)[1].lower()

        if os.path.isdir(path):
            return

        if ext.endswith((".txt", ".qjr", ".json", ".csv", ".py", ".cpp", ".cxx", ".c", ".h", ".asm", ".xml", ".yaml",
                          ".yml", ".toml", ".plist", ".log", ".sh")):

            from qjr_notepad import create_notepad

            editor = create_notepad(self)
            editor.load_file(path)
            editor.show()

        elif path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):

            from qjr_image_viewer import create_image_viewer

            viewer = create_image_viewer(self, path)
            viewer.show()

        elif path.lower().endswith((".mp3", ".wav", ".ogg", ".aiff")):
            from qjr_media_player import create_player

            player = create_player()
            player.load_file(path)  # або будь-який шлях
            player.show()

        elif path.lower().endswith((".mp4", ".avi", ".mkv", ".mov", ".wmv")):
            from qjr_video_player import open_video_player

            if not hasattr(self, "video_player") or self.video_player is None:
                self.video_player = open_video_player(self)

            self.video_player.show()
            self.video_player.raise_()
            self.video_player.activateWindow()

            # передати файл у плеєр
            self.video_player.player.setSource(QUrl.fromLocalFile(path))
            self.video_player.player.play()

        else:
            print("Unknown file type:", path)

    def open_external(self):

        index = self.list.currentIndex()
        if not index.isValid():
            return

        path = self.model.filePath(index)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def on_list_double_clicked(self, index):
        if self.model.isDir(index):
            self.set_path(self.model.filePath(index))
        else:
            self.open_internal(index)

    def closeEvent(self, event):
        global _file_manager_instance
        _file_manager_instance = None
        super().closeEvent(event)

    def create_image_viewer(parent=None, file_path=None):

        viewer = ImageViewer(parent)

        if file_path:
            viewer.load_image(file_path)

        return viewer

    def open_with_video_player(self, path):
        from qjr_video_player import open_video_player

        if not hasattr(self, "video_player") or self.video_player is None:
            self.video_player = open_video_player(self)

        self.video_player.show()
        self.video_player.raise_()
        self.video_player.activateWindow()

        # передати файл у плеєр
        self.video_player.player.setSource(QUrl.fromLocalFile(path))
        self.video_player.player.play()

    def open_with_zip_manager(self, path):
        from qjr_zip_manager import QJRZipManager, CompressDialog, UncompressDialog
        import os

        if path.lower().endswith(".zip"):
            # Якщо ZIP → запитати: розпакувати
            reply = QMessageBox.question(
                self,
                "ZIP file",
                "This is a ZIP archive.\nDo you want to extract it?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                dialog = UncompressDialog(self)
                dialog.zip_file = path
                dialog.show()

        else:
            # Якщо не ZIP → запитати: запакувати
            reply = QMessageBox.question(
                self,
                "Compress",
                "Do you want to compress this file/folder into a ZIP?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                dialog = CompressDialog(self)
                dialog.selected_paths = [path]
                dialog.show()

    # === JSON controls ===

    def load_favorites(self):
        # loading favorites from JSON DB
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    self.favorites = json.load(f)

                # гарантія що це список
                if not isinstance(self.favorites, list):
                    self.favorites = []

            except Exception:
                self.favorites = []
        else:
            self.favorites = []

        self.update_favorites_view()

    def save_favorites(self):
        # favorites saving
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Can't save to favorites:\n{e}")
    #
    # def update_favorites_view(self):
    #     """Оновлення списку Favorites"""
    #     from PySide6.QtGui import QStandardItemModel, QStandardItem
    #
    #     # захист від раннього виклику
    #     if not hasattr(self, "fav_list"):
    #         return
    #
    #     model = QStandardItemModel(self)
    #
    #     for path in self.favorites:
    #         if not isinstance(path, str):
    #             continue
    #
    #         if not os.path.exists(path):
    #             continue
    #
    #         name = os.path.basename(path) or path
    #
    #         item = QStandardItem(name)
    #         item.setData(path, Qt.UserRole)
    #
    #         # (опціонально) іконка
    #         info = QFileInfo(path)
    #         icon = self.model.iconProvider().icon(info)
    #         item.setIcon(icon)
    #
    #         model.appendRow(item)
    #
    #     self.fav_list.setModel(model)
    def update_favorites_view(self):

        model = QStandardItemModel(self)

        # ⭐ FAVORITES

        favorites_root = QStandardItem("⭐ Favorites")
        favorites_root.setEditable(False)

        for path in self.favorites:

            if not os.path.exists(path):
                continue

            name = os.path.basename(path)

            if not name:
                name = path

            item = QStandardItem(name)
            item.setEditable(False)
            item.setData(path, Qt.UserRole)

            info = QFileInfo(path)
            icon = self.model.iconProvider().icon(info)

            item.setIcon(icon)

            favorites_root.appendRow(item)

        model.appendRow(favorites_root)

        # 👤 USER FOLDERS

        user_root = QStandardItem("👤 User")
        user_root.setEditable(False)

        user_path = get_user_fs()

        folders = [
            "backup",
            # "desktop",
            "documents",
            # "downloads",
            "images",
            "logs",
            "music",
            "video"
        ]

        for folder in folders:

            full_path = os.path.join(user_path, folder)

            if not os.path.exists(full_path):
                continue

            item = QStandardItem(folder)
            item.setEditable(False)
            item.setData(full_path, Qt.UserRole)

            info = QFileInfo(full_path)
            icon = self.model.iconProvider().icon(info)

            item.setIcon(icon)

            user_root.appendRow(item)

        model.appendRow(user_root)

        # 💾 DRIVES

        drives_root = QStandardItem("💾 Drives")
        drives_root.setEditable(False)

        for drive in QDir.drives():
            drive_path = drive.absolutePath()

            item = QStandardItem(drive_path)
            item.setEditable(False)
            item.setData(drive_path, Qt.UserRole)

            info = QFileInfo(drive_path)
            icon = self.model.iconProvider().icon(info)

            item.setIcon(icon)

            drives_root.appendRow(item)

        model.appendRow(drives_root)

        # =========================================

        self.fav_tree.setModel(model)

        self.fav_tree.expandAll()

    def open_favorite(self, index):
        """Відкрити favorite"""
        path = index.data(Qt.UserRole)

        if not path:
            return

        if not os.path.exists(path):
            QMessageBox.warning(self, "Error", "Path does not exist")
            return

        if os.path.isdir(path):
            self.set_path(path)
        else:
            # можна замінити на self.open_internal(...) якщо хочеш
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def favorites_context_menu(self, pos):
        """Контекстне меню Favorites"""
        index = self.fav_tree.indexAt(pos)
        menu = QMenu(self)

        add_action = menu.addAction("📂 Add current directory")

        remove_action = None
        if index.isValid():
            remove_action = menu.addAction("❌ Delete")

        action = menu.exec(self.fav_tree.viewport().mapToGlobal(pos))

        # ➕ Додати
        if action == add_action:
            path = self.path_edit.text()

            if path and os.path.exists(path):
                if path not in self.favorites:
                    self.favorites.append(path)
                    self.save_favorites()
                    self.update_favorites_view()

        # ❌ Видалити
        elif remove_action and action == remove_action:
            path = index.data(Qt.UserRole)

            if path in self.favorites:
                self.favorites.remove(path)
                self.save_favorites()
                self.update_favorites_view()

    def create_file_with_ext(self, ext):
        name, ok = QInputDialog.getText(
            self,
            "New File",
            f"Enter filename (*.{ext}):"
        )

        if ok and name:
            if not name.endswith(f".{ext.lower()}"):
                name += f".{ext}"

            path = os.path.join(self.path_edit.text(), name)

            if os.path.exists(path):
                QMessageBox.warning(self, "Error", f"File {name} is already exists!!!")
            else:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        if ext == "py":
                            f.write("# QJR Python file\n\n")
                        elif ext in ["json"]:
                            f.write("{}")
                        elif ext in ["xml"]:
                            f.write("<root>\n\n</root>")
                        elif ext in ["csv"]:
                            f.write("col1,col2\n")
                        elif ext in ["qjr"]:
                            f.write(f"file_type = qjr\ncreation_time = {datetime.now()}")
                        else:
                            f.write("")

                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))


    # === Settings ===

    def load_settings(self):
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def apply_settings(self):
        fm = self.settings.get("file_manager", {})

        icon_size = fm.get("icon_size", 32)
        spacing = fm.get("spacing", 0)
        view_mode = fm.get("view_mode", "list")

        # icon size
        self.list.setIconSize(QSize(icon_size, icon_size))

        # spacing
        self.list.setSpacing(spacing)

        # нормалізація
        view_mode = view_mode.lower()

        if view_mode in ["icon", "іконковий", "значки", "іконки"]:
            self.apply_icon_view()
        elif view_mode in ["list", "списковий", "список"]:
            self.apply_list_view(icon_size)
        else:
            self.apply_list_view(icon_size)  # fallback

    # === Hidden files ===

    def toggle_files_view(self):

        content = ""

        if os.path.exists(self.hidden_files_file):
            with open(self.hidden_files_file, "r") as fileConfig:
                content = fileConfig.read().strip().lower()

        new_value = "hide" if content == "show" else "show"

        with open(self.hidden_files_file, "w") as fileConfig:
            fileConfig.write(new_value)

        # застосування
        if new_value == "show":
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden)
        else:
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)


    def apply_hidden_files_setting(self):
        if os.path.exists(self.hidden_files_file):
            with open(self.hidden_files_file, "r") as fileConfig:
                content = fileConfig.read().strip().lower()

                if content == "show":
                    self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden)
                elif content == "hide":
                    self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
                else:
                    # Якщо вміст некоректний, встановити за замовчуванням
                    self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        else:
            # Якщо файл не існує, створити його з налаштуванням за замовчуванням
            with open(self.hidden_files_file, "w") as fileConfig:
                fileConfig.write("hide")
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)

    def open_with_qjr(self, path):
        if not os.path.exists(path):
            return

        if os.path.isdir(path):
            self.set_path(path)
            return

        ext = os.path.splitext(path)[1].lower()

        # TEXT / CODE
        if ext in (
                ".txt", ".qjr", ".json", ".csv", ".py", ".cpp", ".cxx", ".c", ".h",
                ".asm", ".xml", ".yaml", ".yml", ".toml", ".plist", ".log", ".sh"
        ):
            from qjr_notepad import create_notepad
            editor = create_notepad(self)
            editor.load_file(path)
            editor.show()
            return

        # IMAGE
        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
            from qjr_image_viewer import create_image_viewer
            viewer = create_image_viewer(self, path)
            viewer.show()
            return

        # AUDIO
        if ext in (".mp3", ".wav", ".ogg", ".aiff", ".flac"):
            from qjr_media_player import create_player
            player = create_player(self)
            player.load_file(path)
            player.show()
            return

        # VIDEO
        if ext in (".mp4", ".avi", ".mkv", ".mov", ".wmv"):
            self.open_with_video_player(path)
            return

        # ZIP
        if ext == ".zip":
            self.open_with_zip_manager(path)
            return

        # fallback
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    # === Show event ===

    def showEvent(self, event):
        super().showEvent(event)
        self.findChild(QSplitter).setSizes([300, 400, 500])  # 200, 500, 500 - default


def open_file_manager(parent=None, path=None):
    global _file_manager_instance

    if _file_manager_instance is None:
        _file_manager_instance = FileManagerDialog(parent, path)
    elif path is not None:
        _file_manager_instance.set_path(path)

    _file_manager_instance.setStyleSheet("""
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
            border-radius: 2px;
        }

        QSlider::handle:horizontal {
            background: #c2185b;
            width: 12px;
            margin: -4px 0;
            border-radius: 6px;
        }
    """)

    _file_manager_instance.show()
    _file_manager_instance.raise_()
    _file_manager_instance.activateWindow()