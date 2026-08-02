import json
import os

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QTabWidget,
    QFormLayout, QCheckBox, QComboBox, QSpinBox,
    QPushButton, QHBoxLayout, QApplication, QMessageBox
)
from PySide6.QtGui import QFont

SETTINGS_FILE = "user_settings.json"
showed_info = False

# LOAD / SAVE
def load_settings():
    default = {
        "general": {"fullscreen": False, "resolution": "auto", "font_size": 12},
        "file_manager": {"icon_size": 32, "spacing": 1, "view_mode": "list"},
        "appearance": {"visualizer": True,"theme": "SystemMagenta"}
    }

    if not os.path.exists(SETTINGS_FILE):
        save_settings(default)
        return default

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        save_settings(default)
        return default

    for cat in default:
        if cat not in data:
            data[cat] = default[cat]
        else:
            for key, val in default[cat].items():
                data[cat].setdefault(key, val)

    return data


# def save_settings(data, showed_info = False):
def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # if not showed_info:
    #     QMessageBox.information(None,"Properties", "Settings saved, but to apply them, you need to restart QJRhydro.")
    #     showed_info = True



# SETTINGS DIALOG
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.showed_info = False

        self.setWindowTitle("QJRsettings -> to apply settings, restart QJRhydro")
        self.resize(480, 340)
        self.setModal(False)

        self.settings = load_settings()

        layout = QVBoxLayout(self)

        # tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self.create_general_tab(), "General")
        self.tabs.addTab(self.create_file_manager_tab(), "File Manager")
        self.tabs.addTab(self.create_appearance_tab(), "Appearance")
        self.tabs.addTab(self.create_reset_tab(), "Reset")

        # buttons
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        self.save_btn = QPushButton("Save")
        self.close_btn = QPushButton("Close")

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.close_btn)

        self.save_btn.clicked.connect(self.save)
        self.close_btn.clicked.connect(self.accept)

    # TABS
    def create_general_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.fullscreen_cb = QCheckBox()
        self.fullscreen_cb.setChecked(self.settings["general"]["fullscreen"])

        self.resolution_cb = QComboBox()
        self.resolution_cb.addItems(["auto", "1280x720", "1920x1080", "2560x1440"])
        self.resolution_cb.setCurrentText(self.settings["general"]["resolution"])
        self.font_size_sb = QSpinBox()
        self.font_size_sb.setRange(6, 40)
        self.font_size_sb.setValue(self.settings["general"].get("font_size", 12))

        layout.addRow("Fullscreen mode:", self.fullscreen_cb)
        layout.addRow("Resolution:", self.resolution_cb)
        layout.addRow("Font size:", self.font_size_sb)

        return tab

    def create_file_manager_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.icon_size_sb = QSpinBox()
        self.icon_size_sb.setRange(0, 48)
        self.icon_size_sb.setValue(self.settings["file_manager"]["icon_size"])

        self.spacing_sb = QSpinBox()
        self.spacing_sb.setRange(0, 50)
        self.spacing_sb.setValue(self.settings["file_manager"]["spacing"])

        self.view_mode_cb = QComboBox()
        self.view_mode_cb.addItems(["list", "icon"])
        self.view_mode_cb.setCurrentText(self.settings["file_manager"]["view_mode"])

        layout.addRow("Icon size          :", self.icon_size_sb)
        layout.addRow("Spacing            :", self.spacing_sb)
        layout.addRow("View mode          :", self.view_mode_cb)

        return tab

    def create_appearance_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.visualizer = QCheckBox()
        self.visualizer.setChecked(self.settings["appearance"]["visualizer"])

        layout.addRow("Visualizer: ", self.visualizer)

        self.theme_cb = QComboBox()
        self.theme_cb.addItems(["SystemMagenta"])
        self.theme_cb.setCurrentText(self.settings["appearance"]["theme"])

        layout.addRow("Theme:", self.theme_cb)

        return tab

    def create_reset_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        btn = QPushButton("Reset settings to defaults")
        btn.clicked.connect(self.reset_to_defaults)

        layout.addRow(btn)
        return tab

    # RESET
    def reset_to_defaults(self):
        defaults = {
            "general": {"fullscreen": False, "resolution": "auto", "font_size": 12},
            "file_manager": {"icon_size": 32, "spacing": 1, "view_mode": "list"},
            "appearance": {"visualizer": True ,"theme": "SystemMagenta"}
        }
        save_settings(defaults)
        self.settings = defaults
        self.accept()

    # SAVE
    def save(self):
        self.settings["general"]["fullscreen"] = self.fullscreen_cb.isChecked()
        self.settings["general"]["resolution"] = self.resolution_cb.currentText()
        self.settings["general"]["font_size"] = self.font_size_sb.value()

        self.settings["file_manager"]["icon_size"] = self.icon_size_sb.value()
        self.settings["file_manager"]["spacing"] = self.spacing_sb.value()
        self.settings["file_manager"]["view_mode"] = self.view_mode_cb.currentText()

        self.settings["appearance"]["visualizer"] = self.visualizer.isChecked()
        self.settings["appearance"]["theme"] = self.theme_cb.currentText()

        # save_settings(self.settings, self.showed_info)
        save_settings(self.settings)
        # apply_global_settings(QApplication.instance())

    def closeEvent(self, event):
        self.save()
        event.accept()

def open_settings(parent=None):
    dialog = SettingsDialog(parent)
    dialog.show()

    # for not closing via GC
    if parent:
        parent._settings_dialog_ref = dialog

    return dialog