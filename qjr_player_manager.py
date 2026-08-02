from qjr_media_player import create_player
from PySide6.QtWidgets import QFileDialog

# === ГЛОБАЛЬНИЙ ІНСТАНС ===
_player_instance = None

def get_player(parent=None):
    global _player_instance  # ОБОВ'ЯЗКОВО

    if _player_instance is None:
        _player_instance = create_player(parent)

    return _player_instance

def open_player(parent=None, path=None):
    player = get_player(parent)

    if path:
        player.load_file(path)
    else:
        file_path, _ = QFileDialog.getOpenFileName(
            parent,
            "Open Audio",
            "",
            "Audio Files (*.mp3 *.wav *.ogg)"
        )
        if file_path:
            player.load_file(file_path)

    player.show()
    player.raise_()
    player.activateWindow()

    return player