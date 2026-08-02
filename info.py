from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

def open_info(parent):
    # Створюємо діалог
    dlg = QDialog(parent)
    dlg.setWindowTitle("QJR Info Viewer")
    dlg.resize(300, 200)

    # Основний layout
    layout = QVBoxLayout()
    dlg.setLayout(layout)

    # Текстове поле
    viewer = QTextEdit()
    viewer.setReadOnly(True)
    viewer.setText(f"Q-J-R Hydro v5.2.2\nCore (Kernel) Q-J-R version: 6.7.0\n\n(C) Copyright Q-J-R System Development 2019-2026\nSoftware has fully open source code and is completely free to use!\n(MIT License)")
    layout.addWidget(viewer)

    # Кнопка закриття
    btn_close = QPushButton("Close")
    btn_close.clicked.connect(dlg.close)
    layout.addWidget(btn_close)

    dlg.show()