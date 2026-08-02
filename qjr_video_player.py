import sys

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSizePolicy, QSlider
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class VideoPlayerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("QJR Video Player")
        self.resize(800, 500)

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2f;
            }

            QLabel {
                color: white;
                font-family: Consolas;
                font-size: 12px;
            }

            QPushButton {
                background-color: #c2185b;
                color: white;
                border-radius: 8px;
                padding: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #e91e63;
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

            QPushButton:pressed {
                background-color: #ad1457;
            }
        """)

        self.init_ui()

    # === Main INIT UI ===

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        self.is_muted = False

        # =============== VIDEO =================
        self.video_widget = QVideoWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(self.video_widget, stretch=10)  # 🔥 головний блок

        # ================= INFO =================
        self.info = QLabel("No video file loaded")
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setFixedHeight(24)

        main_layout.addWidget(self.info, stretch=0)

        # =============== TIMELINE =================
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)

        main_layout.addWidget(self.slider, stretch=0)

        # ================= VOLUME ================
        volume_layout = QHBoxLayout()

        self.volume_label = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)  # стандарт

        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_slider)

        main_layout.addLayout(volume_layout)

        # =============== CONTROLS =================
        controls = QHBoxLayout()

        self.open_btn = QPushButton("Open")
        self.play_btn = QPushButton("▶")
        self.pause_btn = QPushButton("⏸")
        self.stop_btn = QPushButton("⏹")
        self.mute_btn = QPushButton("🔊")

        for btn in [self.open_btn, self.play_btn, self.pause_btn, self.stop_btn]:
            btn.setFixedHeight(32) # default 32

        controls.addWidget(self.open_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.pause_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.mute_btn)

        main_layout.addLayout(controls, stretch=0)

        # ================= PLAYER ================
        self.player = QMediaPlayer()

        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.player.setVideoOutput(self.video_widget)

        # ================= SIGNALS =================
        self.open_btn.clicked.connect(self.open_file)
        self.play_btn.clicked.connect(self.player.play)
        self.pause_btn.clicked.connect(self.player.pause)
        self.stop_btn.clicked.connect(self.player.stop)
        self.mute_btn.clicked.connect(lambda: self.toggle_mute(self.volume_slider.value(), self.is_muted))

        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.slider.sliderMoved.connect(self.player.setPosition)

        self.volume_slider.valueChanged.connect(self.change_volume)
    # === Timeline logic ===

    def update_position(self, position):
        self.slider.setValue(position)

    def update_duration(self, duration):
        self.slider.setRange(0, duration)

    # === Mute / Volume logic ===

    def toggle_mute(self, value, is_muted):
        # self.player.setMuted(not self.player.isMuted())
        if is_muted:
            # self.audio_output.setMuted(False)
            self.audio_output.setVolume(value / 100)
            self.mute_btn.setText("🔊")
            self.is_muted = False
        else:
            # self.audio_output.setMuted(True)
            self.audio_output.setVolume(0)
            self.mute_btn.setText("🔇")
            self.is_muted = True

        # self.audio_output.setVolume(value / 100)

    def change_volume(self, value):
        self.audio_output.setVolume(value / 100)

    # === Open/load file ===

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video File",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv)"
        )

        if file_path:
            # self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.info.setText(file_path.split("/")[-1])
            self.player.play()

    # === Player shutdown ===
    def closeEvent(self, event):
        self.player.stop()
        self.player.setSource(QUrl())  # очистити файл
        super().closeEvent(event)


# =================== API FUNCTION =====================

def open_video_player(parent=None):
    dlg = VideoPlayerDialog(parent)
    dlg.show()
    return dlg


# ===================== TEST ===================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    win = open_video_player()
    sys.exit(app.exec())