from PySide6.QtWidgets import (
    QDialog, QFileDialog, QMessageBox,
    QVBoxLayout, QMenuBar, QStatusBar,
    QWidget, QPlainTextEdit, QTextEdit, QPushButton
)
from PySide6.QtCore import QFile, QTextStream, Qt, QRect, QSize, QTimer
from PySide6.QtGui import (QPainter, QColor, QTextFormat, QKeySequence, QAction,
                           QTextCursor, QSyntaxHighlighter, QTextCharFormat,
                           QColor, QFont, QIcon, QPixmap)
import os
import re

# PYTHON SYNTAX HIGHLIGHTER

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # 🔵 ключові слова
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#00ffff"))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = [
            "def", "class", "if", "else", "elif", "while", "for",
            "return", "import", "from", "as", "try", "except",
            "with", "lambda", "pass", "break", "continue", "self",
            "in", "not", "global", "True", "False"
        ]

        for word in keywords:
            pattern = rf"\b{word}\b"
            self.rules.append((re.compile(pattern), keyword_format))

        # інші команди...
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#ff00ff"))
        builtin = [
            "print", "bin", "int", "str", "bool", "float", "input",
            "list", "tuple", "set", "dict", "len", "range", "type", 
            "id", "sum", "min", "max", "abs", "round", "pow", "sorted", 
            "reversed", "enumerate", "zip", "map", "filter", "any", 
            "all", "open", "dir", "help", "eval", "exec", "range",
            "super",

            "__init__", "__file__", "__dict__", "__annotations__",
            "__builtins__", "__doc__", "__loader__", "__name__",
            "__package__", "__spec__"
        ]

        for built in builtin:
            pattern_bi = rf"\b{built}\b"
            self.rules.append((re.compile(pattern_bi), builtin_format))

        # None
        none_format = QTextCharFormat()
        none_format.setForeground(QColor(r"#ff0000"))

        self.rules.append((re.compile(r"\bNone\b"), none_format))

        # 🟡 рядки
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))

        self.rules.append((re.compile(r'"[^"]*"'), string_format))
        self.rules.append((re.compile(r"'[^']*'"), string_format))

        # 🟢 коментарі
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))

        self.rules.append((re.compile(r'(^|[^"\'])#.*'), comment_format))

        # 🔢 числа
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))

        self.rules.append((re.compile(r"\b\d+\b"), number_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

# C++ HIGHLIGHTING BLOCK

class CPPHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # ========= KEYWORDS =========

        keyword = QTextCharFormat()
        keyword.setForeground(QColor("#00ffff"))
        keyword.setFontWeight(QFont.Bold)

        keywords = [
            "alignas", "alignof", "asm", "auto",
            "bool", "break",
            "case", "catch", "char", "char8_t", "char16_t", "char32_t",
            "class", "const", "consteval", "constexpr", "constinit",
            "continue",
            "default", "delete", "do", "double",
            "else", "enum", "explicit", "export", "extern",
            "false", "float", "for", "friend",
            "goto",
            "if", "inline", "int",
            "long",
            "mutable",
            "namespace", "new", "noexcept", "nullptr",
            "operator",
            "private", "protected", "public",
            "register", "reinterpret_cast",
            "return",
            "short", "signed", "sizeof", "static",
            "static_assert", "string", "struct", "switch",
            "template", "this", "thread_local",
            "throw", "true", "try", "typedef",
            "typename",
            "union", "unsigned", "using",
            "virtual", "void", "volatile",
            "while"
        ]

        for word in keywords:
            self.rules.append(
                (re.compile(rf"\b{word}\b"), keyword)
            )

        # ========= TYPES =========

        type_fmt = QTextCharFormat()
        type_fmt.setForeground(QColor("#ff00ff"))

        types = [
            "std", "string", "wstring",
            "vector", "list", "deque",
            "queue", "stack",
            "map", "unordered_map",
            "set", "unordered_set",
            "pair", "tuple",
            "optional", "variant",
            "shared_ptr", "unique_ptr",
            "weak_ptr"
        ]

        for t in types:
            self.rules.append(
                (re.compile(rf"\b{t}\b"), type_fmt)
            )

        # ========= FUNCTIONS =========

        function_fmt = QTextCharFormat()
        function_fmt.setForeground(QColor("#DCDCAA"))

        self.rules.append((
            re.compile(r"\b[A-Za-z_]\w*(?=\()"),
            function_fmt
        ))

        # ========= PREPROCESSOR =========

        pre_fmt = QTextCharFormat()
        # pre_fmt.setForeground(QColor("#C586C0"))
        pre_fmt.setForeground(QColor("#00ffff"))

        self.rules.append((
            re.compile(r"^\s*#.*"),
            pre_fmt
        ))

        # ========= STRINGS =========

        string_fmt = QTextCharFormat()
        string_fmt.setForeground(QColor("#ce9178"))

        self.rules.append((
            re.compile(r'"([^"\\]|\\.)*"'),
            string_fmt
        ))

        self.rules.append((
            re.compile(r"'([^'\\]|\\.)*'"),
            string_fmt
        ))

        # ========= NUMBERS =========

        number_fmt = QTextCharFormat()
        number_fmt.setForeground(QColor("#b5cea8"))

        self.rules.append((
            re.compile(
                r"\b(0x[0-9A-Fa-f]+|0b[01]+|\d+(\.\d+)?)\b"
            ),
            number_fmt
        ))

        # ========= COMMENTS =========

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6a9955"))

        self.rules.append((
            re.compile(r"//.*"),
            comment_fmt
        ))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

# ===============================
# x86 / x86_64 / 8086 ASSEMBLY HIGHLIGHTER
# ===============================

class AssemblyHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # ========= INSTRUCTIONS =========

        instruction_format = QTextCharFormat()
        instruction_format.setForeground(QColor("#00ffff"))
        instruction_format.setFontWeight(QFont.Bold)

        instructions = [
            # Data movement
            "MOV", "MOVZX", "MOVSX", "MOVS", "MOVSB", "MOVSW", "MOVSD", "MOVSQ",
            "XCHG", "PUSH", "POP", "PUSHA", "POPA", "PUSHAD", "POPAD",
            "PUSHF", "POPF", "PUSHFD", "POPFD", "PUSHFQ", "POPFQ",

            # Arithmetic
            "ADD", "ADC", "SUB", "SBB", "MUL", "IMUL",
            "DIV", "IDIV", "INC", "DEC", "NEG", "CMP",

            # Logical
            "AND", "OR", "XOR", "NOT", "TEST",

            # Shifts / rotates
            "SHL", "SAL", "SHR", "SAR",
            "ROL", "ROR", "RCL", "RCR",

            # Jumps
            "JMP", "JE", "JZ", "JNE", "JNZ",
            "JG", "JNLE", "JGE", "JNL",
            "JL", "JNGE", "JLE", "JNG",
            "JA", "JNBE", "JAE", "JNB",
            "JB", "JNAE", "JBE", "JNA",

            # Loop
            "LOOP", "LOOPE", "LOOPZ", "LOOPNE", "LOOPNZ",

            # Calls / returns
            "CALL", "RET", "RETN", "RETF",

            # Stack / flags
            "CLC", "CLD", "CLI", "CMC", "STC",
            "LAHF", "SAHF",

            # Interrupts
            "INT", "IRET", "IRETD", "IRETQ",

            # CPU control
            "NOP", "HLT", "WAIT",

            # String instructions
            "CMPS", "CMPSB", "CMPSW", "CMPSD", "CMPSQ",
            "SCAS", "SCASB", "SCASW", "SCASD", "SCASQ",
            "LODS", "LODSB", "LODSW", "LODSD", "LODSQ",
            "STOS", "STOSB", "STOSW", "STOSD", "STOSQ",

            # Bit operations
            "BT", "BTC", "BTR", "BTS",
            "BSF", "BSR",

            # Conversion
            "CBW", "CWDE", "CDQE",
            "CWD", "CDQ", "CQO",

            # Special
            "CPUID", "RDTSC", "SYSCALL", "SYSRET",
            "SYSENTER", "SYSEXIT",
            "IN", "OUT",

            # x87
            "FLD", "FST", "FSTP",
            "FADD", "FSUB", "FMUL", "FDIV",
            "FINIT", "FNINIT",

            # SIMD
            "XMM", "YMM", "ZMM"
        ]

        for instruction in instructions:
            self.rules.append(
                (
                    re.compile(
                        rf"\b{instruction}\b",
                        re.IGNORECASE
                    ),
                    instruction_format
                )
            )

        # ========= REGISTERS =========

        register_format = QTextCharFormat()
        register_format.setForeground(QColor("#00ffff"))
        register_format.setFontWeight(QFont.Bold)

        registers = [
            # 8086 / 16-bit
            "AX", "BX", "CX", "DX",
            "SP", "BP", "SI", "DI",

            # Segment registers
            "CS", "DS", "ES", "SS", "FS", "GS",

            # Instruction / flags
            "IP", "EIP", "RIP",
            "FLAGS", "EFLAGS", "RFLAGS",

            # 32-bit
            "EAX", "EBX", "ECX", "EDX",
            "ESP", "EBP", "ESI", "EDI",

            # 64-bit
            "RAX", "RBX", "RCX", "RDX",
            "RSP", "RBP", "RSI", "RDI",

            "R8", "R9", "R10", "R11",
            "R12", "R13", "R14", "R15",

            # 8-bit
            "AL", "AH",
            "BL", "BH",
            "CL", "CH",
            "DL", "DH",

            # Extended 8-bit
            "SIL", "DIL", "BPL", "SPL",

            "R8B", "R9B", "R10B", "R11B",
            "R12B", "R13B", "R14B", "R15B",

            # 16-bit extended
            "R8W", "R9W", "R10W", "R11W",
            "R12W", "R13W", "R14W", "R15W",

            # 32-bit extended
            "R8D", "R9D", "R10D", "R11D",
            "R12D", "R13D", "R14D", "R15D",

            # SIMD
            "XMM0", "XMM1", "XMM2", "XMM3",
            "XMM4", "XMM5", "XMM6", "XMM7",
            "XMM8", "XMM9", "XMM10", "XMM11",
            "XMM12", "XMM13", "XMM14", "XMM15",

            "YMM0", "YMM1", "YMM2", "YMM3",
            "YMM4", "YMM5", "YMM6", "YMM7",
            "YMM8", "YMM9", "YMM10", "YMM11",
            "YMM12", "YMM13", "YMM14", "YMM15"
        ]

        for register in registers:
            self.rules.append(
                (
                    re.compile(
                        rf"\b{register}\b",
                        re.IGNORECASE
                    ),
                    register_format
                )
            )

        # ========= DIRECTIVES =========

        directive_format = QTextCharFormat()
        directive_format.setForeground(QColor("#ff00ff"))
        directive_format.setFontWeight(QFont.Bold)

        directives = [
            "section", "segment",
            "global", "extern",
            "bits", "use16", "use32", "use64",
            "org", "align",
            "db", "dw", "dd", "dq",
            "dt", "do",
            "resb", "resw", "resd", "resq",
            "equ",
            "times",
            "byte", "word", "dword", "qword",
            "ptr",
            "assume",
            "public",
            "proc", "endp",
            "model",
            "include",
            "macro", "endm"
        ]

        for directive in directives:
            self.rules.append(
                (
                    re.compile(
                        rf"(?<![\w.])\.?{directive}\b",
                        re.IGNORECASE
                    ),
                    directive_format
                )
            )

        # ========= NUMBERS =========

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))

        number_patterns = [
            r"\b0x[0-9A-Fa-f]+\b",
            r"\b0b[01]+\b",
            r"\b[0-9A-Fa-f]+h\b",
            r"\b[01]+b\b",
            r"\b\d+\b"
        ]

        for pattern in number_patterns:
            self.rules.append(
                (
                    re.compile(pattern, re.IGNORECASE),
                    number_format
                )
            )

        # ========= STRINGS =========

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))

        self.rules.append(
            (
                re.compile(r'"([^"\\]|\\.)*"'),
                string_format
            )
        )

        self.rules.append(
            (
                re.compile(r"'([^'\\]|\\.)*'"),
                string_format
            )
        )

        # ========= LABELS =========

        label_format = QTextCharFormat()
        label_format.setForeground(QColor("#DCDCAA"))
        label_format.setFontWeight(QFont.Bold)

        self.rules.append(
            (
                re.compile(r"^\s*[A-Za-z_.$?][\w.$?]*:"),
                label_format
            )
        )

        # ========= COMMENTS =========

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))

        # NASM / MASM comments
        self.rules.append(
            (
                re.compile(r";.*"),
                comment_format
            )
        )

        # C-style comments
        self.rules.append(
            (
                re.compile(r"//.*"),
                comment_format
            )
        )

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(
                    start,
                    end - start,
                    fmt
                )

class JustHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        # None
        none_format = QTextCharFormat()
        none_format.setForeground(QColor(r"#ff0000"))

        self.rules.append((re.compile(r"\bNone\b"), none_format))

        # 🟡 рядки
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))

        self.rules.append((re.compile(r'"[^"]*"'), string_format))
        self.rules.append((re.compile(r"'[^']*'"), string_format))

        # 🟢 коментарі
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))

        self.rules.append((re.compile(r'(^|[^"\'])#.*'), comment_format))

        # 🔢 числа
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))

        self.rules.append((re.compile(r"\b\d+\b"), number_format))

    def highlightBlock(self, text):

        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)

        # ===== багаторядкові коментарі =====

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6A9955"))

        start = 0

        if self.previousBlockState() != 1:
            start = text.find("/*")

        while start >= 0:

            end = text.find("*/", start)

            if end == -1:
                self.setCurrentBlockState(1)
                length = len(text) - start
            else:
                length = end - start + 2

            self.setFormat(start, length, comment_fmt)

            if end == -1:
                break

            start = text.find("/*", start + length)

        if self.currentBlockState() != 1:
            self.setCurrentBlockState(0)


    # def highlightBlock(self, text):
    #     for pattern, fmt in self.rules:
    #         for match in pattern.finditer(text):
    #             start, end = match.span()
    #             self.setFormat(start, end - start, fmt)

# Line Number Area

class LineNumberArea(QWidget):

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


# Code editor

class CodeEditor(QPlainTextEdit):

    def __init__(self):
        super().__init__()

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):

        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(),
                self.line_number_area.width(),
                rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):

        super().resizeEvent(event)

        cr = self.contentsRect()

        self.line_number_area.setGeometry(
            QRect(
                cr.left(),
                cr.top(),
                self.line_number_area_width(),
                cr.height()
            )
        )


    def line_number_area_paint_event(self, event):
        # Left line number area background

        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():

            if block.isVisible() and bottom >= event.rect().top():

                number = str(block_number + 1)

                painter.setPen(Qt.gray)

                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        # highlight current line background (where's caret)

        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            # lineColor = QColor(235, 235, 255)
            lineColor = QColor(46, 46, 46)

            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)

            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        # TAB → 4 пробіли
        if event.key() == Qt.Key_Tab and not event.modifiers():
            cursor.insertText("    ")
            return

        # Shift+TAB -> видалити 4 пробіли
        elif event.key() == Qt.Key_Backtab:
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, 4)
            if cursor.selectedText() == "    ":
                cursor.removeSelectedText()
            return

        super().keyPressEvent(event)

# QJR Notepad

class QJRNotepad(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("QJR Notepad")
        self.resize(900, 650)

        self.current_file = None

        self.TRIPLE_QUOTE = 1

        layout = QVBoxLayout(self)

        # autosave
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(5000)  # 5 секунд

        # меню
        self.menu_bar = QMenuBar()
        layout.setMenuBar(self.menu_bar)

        # редактор
        self.editor = CodeEditor()
        self.set_highlighter(None)
        layout.addWidget(self.editor)


        # self.highlighter = PythonHighlighter(self.editor.document())

        # status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

        self._create_menu()

        self.editor.textChanged.connect(self.update_status)
        self.editor.cursorPositionChanged.connect(self.update_status)

        self.update_status()

    # FILE ACTIONS

    def new_file(self):

        if self._maybe_save():

            self.editor.clear()
            self.current_file = None
            self.update_status()

    def open_file(self):
        if not self._maybe_save():
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "Default (*.txt *.py *.qjr *.json *.csv *.cpp *.c *.h *.hpp *.plist *.asm *.s *.inc);;All Files (*);;Text Files (*.txt);;Python Files (*.py);;JSON Files (*.json);;Q-J-R Files (*.qjr);;CSV Files (*.csv);;C++/C/Header Files (*.cpp *.c *.h *.hpp);;Plist File (*.plist);;Assembly Files (*.asm *.s *inc)"
        )

        if path:
            file = QFile(path)
            if file.open(QFile.ReadOnly | QFile.Text):
                self.editor.setPlainText(QTextStream(file).readAll())
                file.close()
                self.current_file = path
                self.set_highlighter(path)

                self.update_status()

    def save_file(self):
        if self.current_file:
            self._write(self.current_file)
        else:

            self.save_file_as()

    def save_file_as(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "All Files (*);;Text Files (*.txt);;Python Files (*.py);;Q-J-R Files (*.qjr);;JSON Files (*.json);;CSV Files (*.csv);;C++/C/Header Files (*.cpp *.c *.h *.hpp);;Plist File (*.plist);;Assembly Files (*.asm *.s *.inc)"
        )

        if path:

            self.current_file = path
            self.set_highlighter(path)

            self._write(path)

    def load_file(self, path):

        file = QFile(path)

        if file.open(QFile.ReadOnly | QFile.Text):

            self.editor.setPlainText(QTextStream(file).readAll())

            file.close()

            self.current_file = path
            self.set_highlighter(path)

            self.editor.document().setModified(False)
            self.update_status()

    def duplicate_line(self):
        cursor = self.textCursor()
        cursor.select(cursor.LineUnderCursor)
        text = cursor.selectedText()

        cursor.movePosition(cursor.EndOfLine)
        cursor.insertText("\n" + text)

    def toggle_comment(self):
        cursor = self.textCursor()
        cursor.select(cursor.LineUnderCursor)
        text = cursor.selectedText()

        if text.strip().startswith("#"):
            text = text.replace("#", "", 1)
        else:
            text = "# " + text

        cursor.insertText(text)

    # ==============================
    # HELP MENU
    # ==============================

    def help_combinations(self):
        help_dlg = QDialog(self)
        help_dlg.setWindowTitle("QJR Notepad: Help with Button Combinations Viewer")
        help_dlg.resize(650, 450)

        # Основний layout
        layout = QVBoxLayout()
        help_dlg.setLayout(layout)

        # Текстове поле
        viewer = QTextEdit()
        viewer.setReadOnly(True)
        viewer.setText(
            f"System button : \n 1. Windows = control\n 2. macOS = command\n 3. Linux = control / super\n\nSystem button + N => create new file\nSystem button + O => open existing file\nSystem button + S => save file\nSystem button + Shift + S => save file as...\n\nTAB => Add tabulation\nShift + TAB => Remove tabulation\n\nATTENTION! Some combinations may vary depending on the operating system, names of which are not specified above!\n(C) Copyright Q-J-R System Development 2019-2026")
        layout.addWidget(viewer)

        # Кнопка закриття
        btn_close = QPushButton("Got it, understood")
        btn_close.clicked.connect(help_dlg.close)
        layout.addWidget(btn_close)

        help_dlg.show()

    # ===============================
    # STATUS
    # ===============================

    def update_status(self):

        text = self.editor.toPlainText()

        lines = text.count("\n") + 1 if text else 0
        chars = len(text)

        filename = os.path.basename(self.current_file) if self.current_file else "New File"

        # cursor = self.editor.textCursor()
        #
        # line = cursor.blockNumber() + 1
        # column = cursor.columnNumber() + 1
        cursor = self.editor.textCursor()

        if not self.editor.document().isEmpty():
            line = cursor.blockNumber() + 1
            column = cursor.columnNumber() + 1
        else:
            line = 1
            column = 1

        self.status_bar.showMessage(
            f"{filename} | Strings: {lines} | Symbols: {chars} | Ln {line}, Col {column}"
        )

    # ===============================
    # HELPERS
    # ===============================

    def _write(self, path):

        file = QFile(path)

        if file.open(QFile.WriteOnly | QFile.Text):

            QTextStream(file) << self.editor.toPlainText()

            file.close()

            self.editor.document().setModified(False)

            self.update_status()

    def _maybe_save(self):

        if not self.editor.document().isModified():
            return True

        reply = QMessageBox.question(
            self,
            "Save changes?",
            "The file has unsaved changes. Save?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            self.save_file()
            return True

        if reply == QMessageBox.Cancel:
            return False

        return True

    def autosave(self):
        if not self.editor.document().isModified():
            return

        if self.current_file:
            self._write(self.current_file)

    def _create_menu(self):

        file_menu = self.menu_bar.addMenu("File")

        new_action = QAction("➕ New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_file)

        open_action = QAction("📄 Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)

        save_action = QAction("💾 Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)

        save_as_action = QAction("💿 Save As", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)

        close_action = QAction("⭕️ Close", self)
        close_action.setShortcut(QKeySequence.Close)
        close_action.triggered.connect(self.close)
        close_action.setIconVisibleInMenu(True)

        file_menu.addActions([
            new_action,
            open_action,
            save_action,
            save_as_action,
        ])

        file_menu.addSeparator()
        file_menu.addAction(close_action)

        # help
        help_menu = self.menu_bar.addMenu("Help")
        help_combinations = QAction("❔Keyboard Shortcuts for Quick Work", self)
        help_combinations.setShortcut(QKeySequence.HelpContents)
        help_combinations.triggered.connect(self.help_combinations)
        help_menu.addAction(help_combinations)

    def set_highlighter(self, path: str | None):
        # Deleting previous highlighter
        self.highlighter = None

        if not path:
            self.highlighter = JustHighlighter(self.editor.document())
            return

        ext = os.path.splitext(path)[1].lower()

        match ext:
            case ".py":
                self.highlighter = PythonHighlighter(self.editor.document())

            case ".cpp" | ".cxx" | ".cc" | ".c" | ".hpp" | ".h" | ".hxx":
                self.highlighter = CPPHighlighter(self.editor.document())

            case ".asm" | ".s" | ".inc":
                self.highlighter = AssemblyHighlighter(self.editor.document())

            case _:
                self.highlighter = JustHighlighter(self.editor.document())


# ===============================
# FACTORY FUNCTION
# ===============================

def create_notepad(parent=None, file_path=None):

    editor = QJRNotepad(parent)

    if file_path:
        editor.load_file(file_path)

    return editor