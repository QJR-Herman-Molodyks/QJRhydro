from PySide6.QtWidgets import (
    QDialog, QGridLayout, QPushButton, QLineEdit, QSizePolicy, QWidget
)
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSize, QRect
import math


def style_button(btn, mode="basic"):
    if mode == "basic":
        btn.setMinimumHeight(42)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background: #2a2a2a;
                border-radius: 8px;
                color: white;
            }

            QPushButton:hover {
                background: #d1007a;
            }

            QPushButton:pressed {
                background: #8a0050;
                padding-top: 2px;
                padding-left: 1px;
            }
        """)
    else:
        btn.setMinimumHeight(30)
        btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                background: #2a2a2a;
                border-radius: 6px;
                color: white;
            }

            QPushButton:hover {
                background: #d1007a;
            }

            QPushButton:pressed {
                background: #8a0050;
                padding-top: 1px;
                padding-left: 1px;
            }
        """)

def animate_button(btn):
    # натискання
    btn.setStyleSheet(btn.styleSheet() + """
        QPushButton {
            background: #444;
        }
    """)

    anim = QPropertyAnimation(btn, b"windowOpacity")
    anim.setDuration(80)
    anim.setStartValue(1.0)
    anim.setEndValue(0.85)
    anim.setEasingCurve(QEasingCurve.OutQuad)

    def restore():
        anim2 = QPropertyAnimation(btn, b"windowOpacity")
        anim2.setDuration(120)
        anim2.setStartValue(0.85)
        anim2.setEndValue(1.0)
        anim2.start()
        btn._anim2 = anim2

    anim.finished.connect(restore)
    anim.start()
    btn._anim = anim


def open_calculator(parent):

    dlg = QDialog(parent)
    dlg.setWindowTitle("QJR Calculator")
    dlg.setFixedSize(280, 400)

    dlg.setStyleSheet("""
        QDialog {
            background: #1e1e1e;
            font-family: Consolas;
        }
        QPushButton {
            font-size: 12px;
            background: #2a2a2a;
            border-radius: 6px;
            color: white;
        }
        QPushButton:hover {
            background: #d1007a;
        }
        
        QPushButton:pressed {
            background: #8a0050;
        }
    """)

    layout = QGridLayout(dlg)
    layout.setSpacing(6)
    layout.setContentsMargins(8, 8, 8, 8)

    # ================ DISPLAY =================
    display = QLineEdit()
    display.setReadOnly(True)
    display.setFixedHeight(40)
    layout.addWidget(display, 0, 0, 1, 4)

    # =============== STATE =================
    professional_mode = False
    error_state = False
    buttons = []

    # =============== SAFE EVAL =================
    def safe_eval(expr: str):
        expr = expr.replace("^", "**")
        expr = expr.replace("π", str(math.pi))
        expr = expr.replace("√", "math.sqrt")

        allowed = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log10,
            "sqrt": math.sqrt,
            "math": math,
        }

        return eval(expr, {"__builtins__": {}}, allowed)

    # ================ PRESS LOGIC ================
    def press(text):
        nonlocal error_state

        if error_state:
            display.clear()
            error_state = False

        if text == "C":
            display.clear()
        elif text == "CE":
            display.clear()
        elif text == "⌫":
            display.setText(display.text()[:-1])
        elif text == "=":
            try:
                display.setText(str(safe_eval(display.text())))
            except:
                display.setText("Error")
                error_state = True
        else:
            display.setText(display.text() + text)

    # ================= DATA =================
    basic = [
        ["C", "CE", "⌫", "/"],
        ["7", "8", "9", "*"],
        ["4", "5", "6", "-"],
        ["1", "2", "3", "+"],
        ["0", ".", "^", "="],
    ]

    scientific = [
        ["sin(", "cos(", "tan(", "log("],
        ["√(", "π", "(", ")"],
    ]

    # ================= MODE BUTTON =================
    mode_btn = QPushButton("Enable Professional Mode")
    mode_btn.setFixedHeight(32)
    layout.addWidget(mode_btn, 1, 0, 1, 4)

    # ================ BUTTON AREA =================
    container = QWidget()
    grid = QGridLayout(container)
    grid.setSpacing(6)
    grid.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(container, 2, 0, 1, 4)

    # ================= BUILD BUTTONS ================
    def build_buttons():
        for r in range(7):
            for c in range(4):
                btn = QPushButton("")
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                style_button(btn, "basic")

                btn.clicked.connect(lambda _, b=btn: press(b.text()))
                # btn.clicked.connect(lambda _, b=btn: (animate_button(b), press(b.text())))
                # btn.clicked.connect(lambda _, b=btn: (animate_button(b), press(b.text())))
                grid.addWidget(btn, r, c)
                buttons.append(btn)

    # ================= UPDATE BUTTONS =================
    def update_buttons():
        data = basic + (scientific if professional_mode else [])

        for i, btn in enumerate(buttons):
            r = i // 4
            c = i % 4

            if r < len(data) and c < len(data[r]):
                btn.setText(data[r][c])
                btn.show()

                if professional_mode:
                    style_button(btn, "pro")
                else:
                    style_button(btn, "basic")
            else:
                btn.hide()

        mode_btn.setText(
            "Disable Professional Mode" if professional_mode else "Enable Professional Mode"
        )

    # ================= TOGGLE =================
    def toggle_mode():
        nonlocal professional_mode
        professional_mode = not professional_mode
        update_buttons()

    mode_btn.clicked.connect(toggle_mode)

    # ================= INIT =================
    build_buttons()
    update_buttons()

    # ================= OPEN =================
    # dlg.exec()
    dlg.show()
    return dlg