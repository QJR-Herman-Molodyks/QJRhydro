from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from PySide6.QtCore import Qt

def msg_info(parent, title, text, size_x, size_y, always_on_top=False, modal=False):
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.resize(size_x, size_y)

    # === MAIN ===
    if always_on_top:
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)

    # (make modal)
    if modal:
        dlg.setWindowModality(Qt.ApplicationModal)

    layout = QVBoxLayout()
    dlg.setLayout(layout)

    viewer = QTextEdit()
    viewer.setReadOnly(True)
    viewer.setText(text)
    layout.addWidget(viewer)

    btn_close = QPushButton("Close")
    btn_close.clicked.connect(dlg.close)
    layout.addWidget(btn_close)

    dlg.show()

    return dlg