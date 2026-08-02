from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCalendarWidget,
    QPushButton, QLabel, QHBoxLayout, QLineEdit
)
from PySide6.QtCore import QDate


class QJRCalendar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("QJR Hydro Calendar")
        self.resize(420, 360)

        layout = QVBoxLayout(self)

        # calendar
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True) # Default : true
        self.calendar.selectionChanged.connect(self.update_label)
        self.calendar.setMinimumDate(QDate(1, 1, 1))
        self.calendar.setMaximumDate(QDate(9999, 12, 31))
        print(self.calendar.maximumDate())
        layout.addWidget(self.calendar)

        self.date_label = QLabel()
        layout.addWidget(self.date_label)

        # date input
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        layout.addWidget(self.date_input)

        #button layout

        btn_layout = QHBoxLayout()

        self.today_button = QPushButton("Today")
        self.today_button.clicked.connect(self.go_today)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_selection)

        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.go_to_date)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        btn_layout.addWidget(self.today_button)
        btn_layout.addWidget(self.clear_button)
        btn_layout.addWidget(self.go_button)
        btn_layout.addWidget(self.close_button)

        layout.addLayout(btn_layout)

        self.calendar.setMinimumDate(QDate(2000, 1, 1))
        self.calendar.setMaximumDate(QDate(2100, 12, 31))

        self.go_today()

        # style
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                color: white;
                font-family: Consolas;
            }
            QLabel {
                font-size: 14px;
                padding: 4px;
            }
            QLineEdit {
                background: #2a2a2a;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 6px;
                color: white;
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
            QCalendarWidget {

    background-color: #1e1e2f;
    border: 2px solid #3a3a5a;
    border-radius: 12px;
    color: #ffffff;
    font-family: Consolas;
    font-size: 14px;

}

QCalendarWidget QToolButton {

    background-color: #2a2a40;

    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 6px;
    margin: 2px;
}

QCalendarWidget QToolButton:hover {
    background-color: #3a3a5a;
}

/* Навігаційні стрілки */
QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {
    font-size: 16px;
    width: 30px;
}


QCalendarWidget QHeaderView::section {
    background-color: #2a2a40;
    color: #aaaaee;
    border: none;
    padding: 4px;
    font-weight: bold;
}


QCalendarWidget QTableView {
    background-color: #1e1e2f;
    selection-background-color: #ff00aa;
    selection-color: #ffffff;
}

/* Звичайні дні */
QCalendarWidget QTableView::item {
    padding: 6px;
    border-radius: 6px;
}

/* Hover по датах */
QCalendarWidget QTableView::item:hover {
    background-color: #3a3a5a;
}

/* Поточний день */

QCalendarWidget QTableView::item:selected {
    background-color: #ff00aa;
    color: #ffffff;
    font-weight: bold;
}

/* Вихідні */
QCalendarWidget QTableView::item:enabled:nth-child(6),
QCalendarWidget QTableView::item:enabled:nth-child(7) {
    color: #ff8080;
}

/* Дні не з поточного місяця */
QCalendarWidget QTableView::item:disabled {
    color: #555577;
}

/* Рамка навколо */
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #1e1e2f;
    border-bottom: 1px solid #3a3a5a;
}
            
        """)

    def update_label(self):
        date = self.calendar.selectedDate()
        self.date_label.setText(f"Selected date: {date.toString('yyyy-MM-dd')}")

    def go_today(self):
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.update_label()

    # def clear_selection(self):
    #     self.date_label.setText("Date is not selected!")
    def clear_selection(self):
        self.date_label.setText("Date is not selected!")
        self.calendar.setSelectedDate(QDate())  # скидання дати
        self.date_input.clear()  # ОЧИЩЕННЯ checkbox

    def go_to_date(self):
        text = self.date_input.text()
        date = QDate.fromString(text, "yyyy-MM-dd")

        if date.isValid():
            self.calendar.setSelectedDate(date)
            self.update_label()
            self.date_input.clear()  # ОЧИЩЕННЯ checkbox

        else:
            self.date_label.setText("Invalid date format!")