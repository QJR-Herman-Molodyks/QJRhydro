
# QT imports
from PySide6.QtWidgets import (
    QApplication, QListWidget, QListWidgetItem,
    QDialog, QVBoxLayout, QTextEdit,
    QGridLayout, QPushButton, QLineEdit, QCalendarWidget, QListView, QLabel,
    QMenu
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, Qt, QTimer, QDateTime, QTimeZone, QDate, QSize, QRect, QLocale
from PySide6.QtGui import QIcon, QFont
from PySide6 import __version__

# just imports

from datetime import datetime
import requests
import psutil
import os
import sys
import socket
import platform
import subprocess
import json

# other files and apps

from settings import *
from qjr_notepad import *
from qjr_calendar import QJRCalendar
from calculator import *
from info import open_info
from file_manager import *
from AIchat import *
from storage import *
from qjr_video_player import *
from term_console import open_term_console

from qjr_msg_box import msg_info

# starting

FS = ["activate.py", "calculator.py", "file_manager.py", "info.py", "qjr_notepad.py", "qjr_calendar.py", "qjr_media_player.py", "favorites.json", "defaultShell.qjr", "quickopen_cfg.json", "user_settings.json", "user"]

base_dir = os.path.dirname(os.path.abspath(__file__))

missing_files = []
for file_name_nec in FS:
    required_path = os.path.join(base_dir, file_name_nec)
    if not os.path.exists(required_path):
        missing_files.append(file_name_nec)

if missing_files:
    print("\033[31mNecessary files are missing! Exiting...\033[0m")
    for file_name_nec in missing_files:
        print(f"  - {file_name_nec}")
    sys.exit(1)

# config

i = 0

QUICK_OPEN_FILE = os.path.join(base_dir, "quickopen_cfg.json")

# application

QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar)

print(f"Log: \n[{datetime.now()}] Starting QJRdesktop...")
print(f"[DEBUG] PySide6 version: {__version__}")
# ================= APP =================
app = QApplication(sys.argv)
app.setStyle("Fusion")
# locale = QLocale(QLocale.Ukrainian, QLocale.Ukraine)

app.setStyleSheet("""

/* ===== BASE ===== */

QWidget {
    color: #eaeaea;
}

/* ===== MAIN WINDOWS / DIALOGS ===== */

QMainWindow, QDialog {
    background-color: #121212;
}

/* ===== LIST WIDGETS (desktop, quickopen, etc.) ===== */

QListWidget {
    background: transparent;   /* as in a default Qt */
}

/* елементи списку — мінімальні зміни */

QListWidget::item {
    padding: 4px;
}

/* ===== ELEMENT SELECTION ===== */

QListWidget::item:selected {
    background-color: palette(highlight);
    color: palette(highlighted-text);
}

/* hover without “repainting” */

QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.08);
}

/* ===== BUTTONS (default + light dark fix) ===== */

QPushButton {
    background: palette(button);
    border: 1px solid palette(mid);
    padding: 4px;
    border-radius: 6px;
}

QPushButton:hover {
    background-color: #5a5a5a;
    border-radius: 10px;
}

/* ===== INPUTS ===== */

QLineEdit, QTextEdit {
    background: palette(base);
    border: 1px solid palette(mid);
}

/* ===== MENU ===== */

QMenu {
    background: palette(window);
}

QMenu::item:selected {
    background: palette(highlight);
}

QMenu::separator {
    height: 1px;
    margin: 4px 12px; 
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent,
        stop:0.2 #777,
        stop:0.8 #777,
        stop:1 transparent
    );
}
""")



# font = QFont("Consolas")
def apply_global_settings(app):
    settings = load_settings()

    font_size = settings.get("general", {}).get("font_size", 12)

    font = QFont()
    font.setFamilies(["Consolas", "Menlo", "Monaco", "Courier New"])
    font.setPointSize(font_size)

    app.setFont(font)

apply_global_settings(app)

loader = QUiLoader()

file = QFile(os.path.join(base_dir, "QJRdesktop.ui"))
file.open(QFile.ReadOnly)

window = loader.load(file)   # 🔴 window make HERE
file.close()

def apply_window_settings(window):
    settings = load_settings()

    general = settings.get("general", {})
    fullscreen = general.get("fullscreen", False)
    resolution = general.get("resolution", "auto")

    # fullscreen has priority.
    if fullscreen:
        window.showFullScreen()
        return

    # if NOT a fullscreen -> applying resolution
    if resolution == "auto":
        window.showNormal()
        return

    try:
        w, h = map(int, resolution.split("x"))
        window.resize(w, h)
    except:
        window.showNormal()


# === Find labels ===
time_label = window.findChild(QLabel, "dashboardTime")
if time_label is None:
    raise RuntimeError("dashboardTime not found!")

date_label = window.findChild(QLabel, "dashboardDate")

# ==== TimeZone of Key
# kyiv_tz = QTimeZone(b"Europe/Kyiv")

def update_time():
    # now = QDateTime.currentDateTimeUtc().toTimeZone(kyiv_tz)
    now = QDateTime.currentDateTime()


    time_label.setText(now.toString("HH:mm:ss"))
    date_label.setText(now.toString("dddd, dd MMMM"))

# === Spheres ===

spheres = window.findChild(QListWidget, "spheresList")

# spheres_list = ["Ligvo", "Post Office", "Storage", "Home Hub"]

# Disk Parititions

spheres.clear()
spheres.setIconSize(QSize(16, 16))

def update_disks():
    spheres.clear()
    spheres.setIconSize(QSize(16, 16))

    partitions = psutil.disk_partitions(all=True)

    for part in partitions:
        item = QListWidgetItem(QIcon("icons/storage_new.png"), part.device)

        # SAVING mountpoint
        item.setData(Qt.UserRole, part.mountpoint)

        spheres.addItem(item)

def open_disk(item):
    path = item.data(Qt.UserRole)

    if not path:
        return

    open_file_manager(window, path)


disk_timer = QTimer(window)
disk_timer.timeout.connect(update_disks)
disk_timer.start(2000) # update every 2 seconds

partitions = psutil.disk_partitions(all=True)

for part in partitions:
    spheres.addItem(QListWidgetItem(QIcon("icons/storage_new.png"), part.device))

spheres.itemDoubleClicked.connect(open_disk)

# === Timer ===
# Updating time
timer = QTimer(window)
timer.timeout.connect(update_time)
timer.start(1000)

update_time()

weather_label = window.findChild(QLabel, "weatherLabel")

def get_location():
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=5)
        data = resp.json()

        return {
            "lat": data["latitude"],
            "lon": data["longitude"],
            "city": data.get("city", ""),
            "country": data.get("country_name", "")
        }
    except Exception:
        return None

def update_weather_geo():
    location = get_location()

    if not location:
        weather_label.setText(" 🌦 Weather: unavailable")
        return

    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={location['lat']}"
            f"&longitude={location['lon']}"
            "&current_weather=true"
        )

        resp = requests.get(url, timeout=5)
        data = resp.json()

        weather = data["current_weather"]
        temp = weather["temperature"]
        wind = weather["windspeed"]

        wind_ms = wind / 3.6  # converting km/h in m/s
        status_wind = "null"

        if wind_ms < 0.3:
            status_wind = "Shelter"
        elif wind_ms < 1.5:
            status_wind = "Light breeze"
        elif wind_ms < 3.3:
            status_wind = "Light air"
        elif wind_ms < 5.4:
            status_wind = "Weak breeze"
        elif wind_ms < 7.9:
            status_wind = "Moderate breeze"
        elif wind_ms < 10.7:
            status_wind = "Fresh breeze"
        elif wind_ms < 13.8:
            status_wind = "Strong breeze"
        elif wind_ms < 20.7:
            status_wind = "Storm"
        elif wind_ms < 24.4:
            status_wind = "Strong storm"
        elif wind_ms < 28.4:
            status_wind = "Hurricane"
        elif wind_ms < 36.4:
            status_wind = "Extreme hurricane"
        elif wind_ms < 50.9:
            status_wind = "Violent hurricane"
        elif wind_ms < 60.7:
            status_wind = "Collapse"
        elif wind_ms < 77.4:
            status_wind = "Peak Collapse"

        else:
            status_wind = "null"

        place = location["city"]
        if place:
            weather_label.setText(
                f" 🌦 {place}: {temp} °C | Wind: {wind} km/h ({wind_ms:.1f} m/s) | {status_wind}"
            )
        else:
            weather_label.setText(
                f" 🌦 {temp} °C | Wind: {wind} km/h"
            )

    except Exception as e:
        weather_label.setText(f" 🌦 Weather: unavailable - {e}")

weather_timer = QTimer(window)
weather_timer.timeout.connect(update_weather_geo)
weather_timer.start(600_000)  # 10 хв

update_weather_geo()

low_battery_shown = False

def update_battery():
    global low_battery_shown

    try:
        battery = psutil.sensors_battery()

        if battery is None:
            battery_label.setText("🔌 Battery: N/A")
            return

        percent = int(battery.percent)
        plugged = battery.power_plugged


        if percent > 30:
        # if percent > 90:
            statusBatteryEmoji = "🔋"
            low_battery_shown = False  # скидаємо

        else:
            statusBatteryEmoji = "🪫"

            if not low_battery_shown:
                msg_info(window,
                         "🪫Low battery charge!!!",
                         f"🪫Low battery charge!\nYour device may discharge soon!\n🪫Percentage remaining: {percent}%",
                         size_x=300, size_y=150, always_on_top=True)
                low_battery_shown = True

        if plugged:
            battery_label.setText(f" {statusBatteryEmoji} Battery: {percent}% ⚡")
        else:
            battery_label.setText(f" {statusBatteryEmoji} Battery: {percent}%")

    except Exception as e:
        battery_label.setText(f" 🪫 Battery: unavailable - {e}")


battery_label = window.findChild(QLabel, "batteryLabel")

battery_timer = QTimer(window)
battery_timer.timeout.connect(update_battery)
battery_timer.start(5_000)  # every 5 seconds

update_battery()

# ================= DESKTOP =================

desktop = window.findChild(QListWidget, "desktop")

if desktop is None:
    raise RuntimeError("QListWidget 'desktop' not found!!!")

def open_desktop_menu(pos):
    item = desktop.itemAt(pos)
    if not item:
        return

    menu = QMenu(window)
    add_quick = menu.addAction(" 📌 Pin to QuickOpen Panel")

    action = menu.exec(desktop.mapToGlobal(pos))
    if action == add_quick:
        add_to_quick_open(item)

def remove_from_quick_open(item):
    row = window.quickOpenList.row(item)
    removed_name = item.text()

    window.quickOpenList.takeItem(row)

    save_quick_open()
    print(f"[{datetime.now()}] Removed from QuickOpen: {removed_name}")

def save_quick_open():
    data = []

    for i in range(window.quickOpenList.count()):
        item = window.quickOpenList.item(i)

        data.append({
            "name": item.text(),
            "app_id": item.data(Qt.UserRole),
            "icon": item.data(Qt.UserRole + 1)
        })

    with open(QUICK_OPEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_quick_open_from_file():
    if not os.path.exists(QUICK_OPEN_FILE):
        return

    try:
        with open(QUICK_OPEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        window.quickOpenList.clear()

        for entry in data:
            name = entry.get("name")
            app_id = entry.get("app_id")
            icon_path = entry.get("icon")

            item = QListWidgetItem(QIcon(icon_path), name)
            item.setData(Qt.UserRole, app_id)
            item.setData(Qt.UserRole + 1, icon_path)

            window.quickOpenList.addItem(item)

    except Exception as e:
        print("Load error:", e)

def add_to_quick_open(item):
    name = item.text()
    app_id = item.data(Qt.UserRole)
    icon = item.icon()

    icon_path = None
    for n, path, a_id in apps:
        if a_id == app_id:
            icon_path = path
            break

    for i in range(window.quickOpenList.count()):
        existing = window.quickOpenList.item(i)

        if existing.data(Qt.UserRole) == app_id:
            msg_info(window, title="Error!", text="This item already exists on the panel!!!", size_x=300,
                     size_y=150)
            return

    new_item = QListWidgetItem(QIcon(icon_path), name)
    new_item.setData(Qt.UserRole, app_id)
    new_item.setData(Qt.UserRole + 1, icon_path)  # saving path

    window.quickOpenList.addItem(new_item)

    save_quick_open()

def open_quick_menu(pos):
    list_widget = window.quickOpenList
    item = list_widget.itemAt(pos)

    if not item:
        return

    menu = QMenu(window)
    remove_action = menu.addAction("❌ Remove from QuickOpen Panel")

    action = menu.exec(list_widget.mapToGlobal(pos))

    if action == remove_action:
        remove_from_quick_open(item)

desktop.setViewMode(QListView.IconMode)
desktop.setMovement(QListView.Free)
desktop.setDragDropMode(QListWidget.InternalMove)

desktop.setResizeMode(QListView.Adjust)
desktop.setFlow(QListView.LeftToRight)
desktop.setWrapping(True)

desktop.setSpacing(12)
desktop.setGridSize(QSize(100, 100))

desktop.setDragEnabled(True)
desktop.setAcceptDrops(True)
desktop.setDropIndicatorShown(True)

# Custom context menu for QuickOpen Panel

desktop.setContextMenuPolicy(Qt.CustomContextMenu)
desktop.customContextMenuRequested.connect(lambda pos: open_desktop_menu(pos))

window.quickOpenList.setContextMenuPolicy(Qt.CustomContextMenu)
window.quickOpenList.customContextMenuRequested.connect(open_quick_menu)

# DASHBOARD CALENDAR
kyiv_tz = QTimeZone(b"Europe/Kyiv")

calendar = window.findChild(QCalendarWidget, "calendar")
btn_today = window.findChild(QPushButton, "btnToday")

def go_today():
    today = QDateTime.currentDateTimeUtc().toTimeZone(kyiv_tz).date()
    calendar.setSelectedDate(today)
    # calendar.showSelectedDate()

btn_today.clicked.connect(go_today)

# already select QuickOpen at start
go_today()

# Network status

def get_network_status():
    try:
        # basic Internet-connection check
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        connected = True
    except OSError:
        connected = False

    if not connected:
        return "No connection"

    system = platform.system()

    # ===== Windows =====
    if system == "Windows":
        try:
            output = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                encoding="utf-8",
                errors="ignore"
            )
            if "SSID" in output:
                return "Wi-Fi (connected)"
        except:
            pass
        return "Ethernet (connected)"

    if system == "Darwin":
        try:
            route = subprocess.check_output(
                ["route", "get", "default"],
                encoding="utf-8"
            )

            if "interface: en" in route:
                iface = route.split("interface:")[1].split("\n")[0].strip()

                # check whether it is a Wi-Fi
                wifi = subprocess.check_output(
                    ["networksetup", "-listallhardwareports"],
                    encoding="utf-8"
                )

                if f"Device: {iface}" in wifi and "Wi-Fi" in wifi:
                    return "Wi-Fi"

                if iface.startswith("en"):
                    return "Ethernet (зʼєднано)"

            return "Підʼєднано"
        except Exception as e:
            return "Підʼєднано"
#===== Linux =====
    if system == "Linux":
        try:
            output = subprocess.check_output(
                ["iwgetid"],
                encoding="utf-8"
            )
            if output.strip():
                return "Wi-Fi (зʼєднано)"
        except:
            pass
        return "Ethernet (зʼєднано)"

    return "Підʼєднано"

def update_network():
    status = get_network_status()
    networkLabel.setText(f" 🛜 Network: {status}")

networkLabel = window.findChild(QLabel, "networkLabel")

update_network()  # одразу при старті

networkTimer = QTimer(window)
networkTimer.timeout.connect(update_network)
networkTimer.start(5000)


# ================= APPS =================
apps = [
    ("Storage", "icons/storage_new.png", "storage"),
    ("Notepad", "icons/notepad_middle.png", "notepad"),
    ("Calculator", "icons/calc.png", "calculator"),
    ("Sys Info", "icons/info.png", "info"),
    ("AI", "icons/ai-robot.png", "ai"),
    ("Calendar", "icons/calendar.png", "calendar"),
    ("Console", "icons/console.png", "console_term"),
    ("Diagram", "icons/diagram.png", "diagrams"),
    ("Exit", "icons/exit.png", "exit"),

    ("File Manager", "icons/filemgr_new.png", "filemgr"),
    ("Image viewer", "icons/image_viewer.png", "image_viewer"),
    ("Music Media", "icons/media_player.png", "media_player"),
    ("Video Player", "icons/video_player.png", "video_player"),
    ("Archive Manager", "icons/zip_mgr.png", "zip_manager"),
    ("Settings", "icons/settings.png", "settings"),
]


def load_quick_open(ui):

    ui.quickOpenList.clear()

    for name, icon, program in quick_open_apps:
        item = QListWidgetItem()
        item.setText(name)
        item.setIcon(QIcon(icon))

        item.setData(Qt.ItemDataRole.UserRole, program)

        ui.quickOpenList.addItem(item)


def quick_open_clicked(item):
    program = item.data(Qt.ItemDataRole.UserRole)
    open_app(program)

# load_quick_open(window)
load_quick_open_from_file()

if window.quickOpenList.count() == 0:
    load_quick_open(window)
    save_quick_open()

window.quickOpenList.itemDoubleClicked.connect(quick_open_clicked)


for name, icon, app_id in apps:
    # icon.setIconSize(QSize(64, 64))  # встановити розмір іконки
    item = QListWidgetItem(QIcon(icon), name)
    item.setData(Qt.UserRole, app_id)
    item.setFlags(
        Qt.ItemIsEnabled
        | Qt.ItemIsSelectable
        | Qt.ItemIsDragEnabled
    )
    desktop.addItem(item)

# ================= PROGRAMS =================
def open_notepad(parent):
    dlg = QDialog(parent)
    dlg.setWindowTitle("QJR Notepad")
    dlg.resize(500, 400)
    layout = QVBoxLayout(dlg)
    layout.addWidget(QTextEdit())
    dlg.show()


def open_app(app_id):
    if app_id == "notepad":
        QJRNotepad(window).show()
    elif app_id == "calculator":
        open_calculator(window)
    elif app_id == "info":
        open_info(window)
    elif app_id == "exit":
        exit()
    elif app_id == "filemgr":
        open_file_manager()
    elif app_id == "settings":
        open_settings(window)
    elif app_id == "storage":
        if not hasattr(window, "dlg_storage"):
            window.dlg_storage = show_storage_dialog(window)
        else:
            window.dlg_storage.show()

        window.dlg_storage.raise_()
        window.dlg_storage.activateWindow()
    elif app_id == "diagrams":
        def open_diagrams():
            from diagrams_graphics import create_diagrams_graphics

            win = create_diagrams_graphics()
            win.show()
        open_diagrams()
    elif app_id == "calendar":
        QJRCalendar(window).show()
    elif app_id == "image_viewer":
        from qjr_image_viewer import ImageViewer
        ImageViewer(window).show()

    elif app_id == "media_player":
        from qjr_player_manager import open_player
        open_player(window)

    elif app_id == "zip_manager":
        from qjr_zip_manager import open_zip_manager
        open_zip_manager(window)

    elif app_id == "ai":
       if not hasattr(window, "dlg_ai"):
           window.dlg_ai = GeminiDialog()
       window.dlg_ai.show()
       window.dlg_ai.raise_()
       window.dlg_ai.activateWindow()

    elif app_id == "video_player":
        if not hasattr(window, "video_player"):
            window.video_player = open_video_player(window)
        window.video_player.show()
        window.video_player.raise_()
        window.video_player.activateWindow()

    elif app_id == "console_term":
        open_term_console(window)

    else:
        print(f"[{datetime.now()}] Open -> ", app_id)


desktop.itemDoubleClicked.connect(
    lambda item: open_app(item.data(Qt.UserRole))
)

apply_window_settings(window)

# якщо fullscreen не увімкнений -> показуємо звичайно
if not window.isFullScreen():
    window.show()

sys.exit(app.exec())
