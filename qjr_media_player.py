from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSlider, QMenuBar
)
from PySide6.QtCore import Qt, QUrl, QFileInfo
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class QJRMediaPlayer(QDialog):

    _player_instance = None   # синглтон збережений

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("QJR Media Player")
        self.setMinimumSize(420, 220)

        # Backend
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.current_path = None

        # Config

        self.set_mute_active = False
        self.set_playing = False

        # === Layouts ===
        main_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        controls_layout = QHBoxLayout()
        progress_layout = QHBoxLayout()

        # === Header ===
        self.label = QLabel("No loaded file!")
        self.label.setAlignment(Qt.AlignCenter)

        self.btn_open = QPushButton("📂")
        self.btn_open.setFixedWidth(40)

        if self.set_mute_active:
            self.btn_mute = QPushButton("🔇")

        else:
            self.btn_mute = QPushButton("🔊")

        self.btn_mute.setFixedWidth(40) #default 40, але можна змінити

        header_layout.addWidget(self.label)
        header_layout.addWidget(self.btn_open)
        header_layout.addWidget(self.btn_mute)

        # === Controls ===
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedWidth(40)
        self.btn_play.setFixedHeight(40)

        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setFixedWidth(40)
        self.btn_stop.setFixedHeight(40)

        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_stop)
        controls_layout.addStretch()

        # === Progress ===
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFixedWidth(100)

        progress_layout.addWidget(self.slider)
        progress_layout.addWidget(self.time_label)

        # === Volume ===
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(50)

        # === Menu Bar ===
        self.menu_bar = QMenuBar()
        main_layout.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu("File")

        open_action = QAction("⬇️ Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)

        exit_action = QAction("⭕️ Close", self)
        exit_action.setShortcut(QKeySequence.Close)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # === Assemble ===
        main_layout.addLayout(header_layout)
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(progress_layout)
        main_layout.addWidget(QLabel("Звук"))
        main_layout.addWidget(self.volume)
        self.setLayout(main_layout)

        # === Styling ===
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
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #c2185b;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)

        # === Signals ===
        self.btn_open.clicked.connect(self.open_file)
        self.btn_stop.clicked.connect(self.player_stop)
        self.btn_play.clicked.connect(self.toggle_play_pause)

        self.volume.valueChanged.connect(
            lambda v: self.audio_output.setVolume(v / 100)
        )

        self.btn_mute.clicked.connect(self.toggle_mute)

        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.slider.sliderReleased.connect(self.seek_release)

        self.player.errorOccurred.connect(self.handle_error)

    # === STOP ===

    def player_stop(self):
        self.player.stop()
        self.btn_play.setText("▶")
        self.set_playing = False

    # === PLAY/PAUSE TOGGLE ===

    def toggle_play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶")
        else:
            self.player.play()
            self.btn_play.setText("⏸")

    # === MUTE TOGGLE ===

    def toggle_mute(self):
        self.set_mute_active = not self.set_mute_active
        self.audio_output.setMuted(self.set_mute_active)
        if self.set_mute_active:
            self.btn_mute.setText("🔇")
        else:
            self.btn_mute.setText("🔊")

    # === FILE LOADING ===
    def load_file(self, path: str):
        if not path:
            self.label.setText("Немає завантаженого файлу")
            return

        info = QFileInfo(path)
        if not info.exists():
            self.label.setText("Файл не знайдений!")
            return

        self.current_path = path
        self.player.setSource(QUrl.fromLocalFile(path))
        self.label.setText(info.fileName())

    # === PROGRESS ===
    def update_position(self, pos):
        if self.player.duration() > 0:
            percent = int(pos / self.player.duration() * 100)
            self.slider.setValue(percent)
        self.update_time()

    def update_duration(self, dur):
        self.update_time()

    def update_time(self):
        pos = self.player.position() // 1000
        dur = self.player.duration() // 1000

        def fmt(t):
            return f"{t//60:02}:{t%60:02}"

        self.time_label.setText(f"{fmt(pos)} / {fmt(dur)}")

    def seek_release(self):
        if self.player.duration() > 0:
            new_pos = int(self.slider.value() / 100 * self.player.duration())
            self.player.setPosition(new_pos)

    # === FILE DIALOG (ручний) ===
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Відкрити аудіо",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.aiff)"
        )
        if file_path:
            self.btn_play.setText("▶")
            self.load_file(file_path)

    # === ERROR ===
    def handle_error(self, err, text):
        self.label.setText(f"ПОМИЛКА: {text}")

    # === СИНГЛТОН  ===
    def get_player(parent=None):
        if QJRMediaPlayer._player_instance is None:
            QJRMediaPlayer._player_instance = create_player(parent)
        return QJRMediaPlayer._player_instance

    def closeEvent(self, event):
        self.player.stop()
        self.player.setSource(QUrl())  # очистити файл
        self.btn_play.setText("▶")
        super().closeEvent(event)

    def open_player(parent=None, path=None):
        player = QJRMediaPlayer.get_player(parent)

        if path:
            player.load_file(path)
        else:
            player.label.setText("No loaded file.")  # clean start screen

        player.show()
        player.raise_()
        player.activateWindow()

        return player


def create_player(parent=None):
    return QJRMediaPlayer(parent)