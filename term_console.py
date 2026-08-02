import shutil

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QPlainTextEdit,
    QLineEdit,
    QApplication,
    QMessageBox,
    QMenuBar,
)

from PySide6.QtGui import QAction, QTextCursor, QFont
from PySide6.QtCore import Qt, QProcess

import os
import platform
import sys
import hashlib
import datetime


# ============================================
# GLOBAL INSTANCE
# ============================================

_terminal_instance = None


# ============================================
# TERMINAL
# ============================================

class QJRTerminal(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("QJR Hydro Console")
        self.resize(1000, 650)

        self.current_shell = "qjr"

        self.cwd = os.getcwd()


        # ====================================
        # LAYOUT
        # ====================================

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ====================================
        # MENUBAR
        # ====================================

        self.menubar = QMenuBar()

        file_menu = self.menubar.addMenu("File")

        clear_action = QAction("🗑️ Clear", self)
        clear_action.triggered.connect(self.clear_terminal)

        exit_action = QAction("⭕️ Exit", self)
        exit_action.triggered.connect(self.close)

        file_menu.addAction(clear_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        terminal_menu = self.menubar.addMenu("Terminal")

        stop_action = QAction("⭕️ Stop Process", self)
        stop_action.triggered.connect(self.stop_process)

        terminal_menu.addAction(stop_action)

        shell_menu = self.menubar.addMenu("Shell")

        QJRhydroConsole = QAction("QJRhydro console", self)
        QJRhydroConsole.triggered.connect(self.set_qjr_shell)
        shell_menu.addAction(QJRhydroConsole)

        shell_menu.addSeparator()

        if os.path.exists("/bin/sh"):
            sh_action = QAction("/bin/sh", self)
            # sh_action.triggered.connect(self.exc_sh)
            sh_action.triggered.connect(self.set_sh_shell)
            shell_menu.addAction(sh_action)

        if os.path.exists("/bin/bash"):
            bash_action = QAction("/bin/bash", self)
            # bash_action.triggered.connect(self.exc_bash)
            bash_action.triggered.connect(self.set_bash_shell)
            shell_menu.addAction(bash_action)

        if os.path.exists("/bin/zsh"):
            zsh_action = QAction("/bin/zsh", self)
            # zsh_action.triggered.connect(self.exc_zsh)
            zsh_action.triggered.connect(self.set_zsh_shell)
            shell_menu.addAction(zsh_action)

        if os.path.exists("/usr/bin/python3"):
            shell_menu.addSeparator()
            python3_action = QAction("/usr/bin/python3", self)
            python3_action.triggered.connect(self.set_python3_shell)
            shell_menu.addAction(python3_action)
        else:
            shell_menu.addSeparator()
            python3_path = shutil.which("python3")
            if python3_path is None:
                python3_path = shutil.which("python")
                if python3_path is None:
                    self.print_line("[Could not find python3]")

        shell_menu.addSeparator()

        default_shell_menu = shell_menu.addMenu("Default Shell")

        default_qjr = QAction("QJRhydro console", self)
        default_qjr.triggered.connect(
            lambda: self.set_default_shell("qjr")
        )
        default_shell_menu.addAction(default_qjr)

        default_zsh = QAction("/bin/zsh", self)
        default_zsh.triggered.connect(
            lambda: self.set_default_shell("/bin/zsh")
        )
        default_shell_menu.addAction(default_zsh)

        default_bash = QAction("/bin/bash", self)
        default_bash.triggered.connect(
            lambda: self.set_default_shell("/bin/bash")
        )
        default_shell_menu.addAction(default_bash)

        default_sh = QAction("/bin/sh", self)
        default_sh.triggered.connect(
            lambda: self.set_default_shell("/bin/sh")
        )
        default_shell_menu.addAction(default_sh)

        layout.addWidget(self.menubar)

        # ====================================
        # OUTPUT
        # ====================================

        self.output = QPlainTextEdit()

        self.output.setReadOnly(True)

        font = QFont("Consolas")
        font.setPointSize(11)

        self.output.setFont(font)

        # ====================================
        # INPUT
        # ====================================

        self.input = QLineEdit()

        self.input.setFont(font)

        self.input.returnPressed.connect(
            self.execute_command
        )

        self.input.setPlaceholderText(
            "Enter command..."
        )

        # ====================================
        # ADD WIDGETS
        # ====================================

        layout.addWidget(self.output)
        layout.addWidget(self.input)

        # ====================================
        # PROCESS
        # ====================================

        self.process = QProcess(self)

        self.current_shell = self.load_default_shell()

        # self.print_line(
        #     f"[Default shell: {self.current_shell}]"
        # )

        self.process.readyReadStandardOutput.connect(
            self.handle_stdout
        )

        self.process.readyReadStandardError.connect(
            self.handle_stderr
        )

        self.process.started.connect(self.handle_python_started)

        # ====================================
        # STYLE
        # ====================================

        self.setStyleSheet("""

            QDialog {
                background: black;
            }

            QPlainTextEdit {
                background: #050505;
                color: #00ff66;
                border: none;
                padding: 8px;
                selection-background-color: #00aa44;
            }

            QLineEdit {
                background: #0d0d0d;
                color: #00ff66;
                border: 1px solid #00aa44;
                padding: 6px;
            }

        """)

        # ====================================
        # START TEXT
        # ====================================

        self.print_line("QJR Hydro Console")
        self.print_line("Hack the planet.")
        self.print_line("")
        self.print_line(f"OS      -> {platform.system()}")
        self.print_line(f"Release -> {platform.release()}")
        self.print_line(f"Time    -> {datetime.datetime.now()}")
        self.print_line("")
        self.print_line(f"Shell   -> {self.current_shell}")

    # ========================================
    # PRINT
    # ========================================

    def print_line(self, text):
        self.output.appendPlainText(text)
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.output.setTextCursor(cursor)

    # ========================================
    # EXECUTE
    # ========================================

    # # macOS / Linux
    #
    # if os.name == "posix":
    #
    #     self.process.start(
    #         "/bin/bash",
    #         ["-c", command]
    #     )
    #
    # # Windows
    #
    # else:
    #
    #     self.process.start(
    #         "cmd.exe",
    #         ["/c", command]
    #     )

    # def set_default_shell(self, shell):
    #     if shell in ["qjr", "/bin/sh", "/bin/bash", "/bin/zsh", "/usr/bin/python3", r"C:\Windows\System32\cmd.exe"]:
    #         try:
    #             with open("defaultShell", "w") as f:
    #                 f.write(shell)
    #         except Exception as e:
    #             QMessageBox.critical(self, "Setting default shell error",f"\nCan't set your default shell\nCritical error occurred: {e}")
    #     else:
    #         QMessageBox.critical(self, "Setting default shell error",f"\nInvalid shell specified: {shell}")

    def set_default_shell(self, shell):
        try:
            with open("defaultShell.qjr", "w", encoding="utf-8") as f:
                f.write(shell)

            self.print_line(f"[Default shell set to {shell}]")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Setting default shell error",
                f"Can't set default shell:\n{e}"
            )

    def load_default_shell(self):
        if not os.path.exists("defaultShell.qjr"):
            return "qjr"

        try:
            with open("defaultShell.qjr", "r", encoding="utf-8") as f:
                return f.read().strip()

        except Exception:
            return "qjr"

    def set_qjr_shell(self):
        self.current_shell = "qjr"
        self.print_line("[Switched to QJR Hydro Console]")

    def set_sh_shell(self):
        self.current_shell = "/bin/sh"
        self.print_line("[Switched to /bin/sh]")

    def set_bash_shell(self):
        self.current_shell = "/bin/bash"
        self.print_line("[Switched to /bin/bash]")

    def set_zsh_shell(self):
        self.current_shell = "/bin/zsh"
        self.print_line("[Switched to /bin/zsh]")

    def set_python3_shell(self):
        self.current_shell = "/usr/bin/python3"
        self.print_line("[Switched to Python 3]")
        self.print_line("[Python commands will run in a persistent interactive session]")

    def set_default_python3_shell(self):
        self.py3_shell_path = shutil.which("python3")

        if self.py3_shell_path is None:
            self.print_line("[Can't find python3 shell: impossible to load it]")
        else:
            self.current_shell = "python3"
            self.print_line(f"[Switched to {self.current_shell}]")


    def set_win32_cmd(self):
        self.current_shell = r"C:\Windows\System32\cmd.exe"
        self.print_line(r"[Switched to C:\Windows\System32\cmd.exe]")


    def exc_win32_cmd(self):
        command = self.input.text().strip()
        if not command:
            return

        if command == "clear":
            self.clear_terminal()
            return
        elif command == "exit":
            self.close()
            return
        elif command.startswith("cd "):
            directory = command[len("cd ") :]
            self.cwd = os.path.abspath(os.path.join(self.cwd, directory))

        self.print_line(f"> {command}")
        self.input.clear()

        self.process.setWorkingDirectory(self.cwd)

        self.process.start(
            "cmd.exe",
            ["/c", command]
        )

    def exc_sh(self):
        command = self.input.text().strip()

        if not command:
            return
        elif command == "clear":
            self.clear_terminal()
            return
        elif command == "exit":
            self.close()
            return
        elif command.startswith("cd "):
            directory = command[len("cd ") :]
            self.cwd = os.path.abspath(os.path.join(self.cwd, directory))

        self.print_line(f"> {command}")
        self.input.clear()

        self.process.setWorkingDirectory(self.cwd)

        self.process.start(
            "/bin/sh",
            ["-c", command]
        )

    def exc_bash(self):
        command = self.input.text().strip()

        if not command:
            return
        elif command == "clear":
            self.clear_terminal()
            return
        elif command == "exit":
            self.close()
            return
        elif command.startswith("cd "):
            directory = command[len("cd ") :]
            self.cwd = os.path.abspath(os.path.join(self.cwd, directory))

        self.print_line(f"> {command}")
        self.input.clear()

        self.process.setWorkingDirectory(self.cwd)

        self.process.start(
            "/bin/bash",
            ["-c", command]
        )

    def exc_zsh(self):
        command = self.input.text().strip()

        if not command:
            return
        elif command == "clear":
            self.clear_terminal()
            return
        elif command == "exit":
            self.close()
            return
        elif command.startswith("cd "):
            directory = command[len("cd ") :]
            self.cwd = os.path.abspath(os.path.join(self.cwd, directory))

        self.print_line(f"> {command}")
        self.input.clear()

        self.process.setWorkingDirectory(self.cwd)

        self.process.start(
            "/bin/zsh",
            ["-c", command]
        )

    def execute_command(self):
        if self.current_shell == "qjr":
            self.exc_qjrshell()
        elif self.current_shell == "/bin/sh":
            self.exc_sh()
        elif self.current_shell == "/bin/bash":
            self.exc_bash()
        elif self.current_shell == "/bin/zsh":
            self.exc_zsh()
        elif self.current_shell == "/usr/bin/python3":
            self.exc_py3()
        elif self.current_shell == r"C:\Windows\System32\cmd.exe":
            self.exc_win32_cmd()
        else:
            self.exc_qjrshell()

    def exc_py3(self):
        command = self.input.text().strip()
        if not command:
            return

        if command == "clear":
            self.clear_terminal()
            return

        if command == "exit()":
            if command in ("exit()", "exit", "quit()", "quit"):
                self.input.clear()
                self.print_line("[Exiting Python Shell]")

                # Ending persistent Python process
                if self.process.state() != QProcess.NotRunning:
                    self.process.write(b"exit()\n")

                    if not self.process.waitForFinished(500):
                        self.process.kill()
                        self.process.waitForFinished(500)

                # Повертаємося до Default Shell
                self.current_shell = self.load_default_shell()

                self.print_line(
                    f"[Switched to default shell: {self.current_shell}]"
                )

                return

        self.print_line(f">>> {command}")
        self.input.clear()

        # Persistent Python interpreter: variables/imports/state survive
        # between commands. The interpreter is started only once.
        if self.process.state() == QProcess.NotRunning:
            python_path = shutil.which("python3") or shutil.which("python") or sys.executable
            self.process.start(
                python_path,
                ["-i", "-u"]
            )

            if not self.process.waitForStarted(1000):
                self.print_line("[Could not start Python interpreter]")
                return

        self.process.write((command + "\n").encode())

    def handle_python_started(self):
        if self.current_shell == "/usr/bin/python3":
            self.print_line("[Python 3 interactive session started]")

    def exc_qjrshell(self):

        command = self.input.text().strip()

        if not command:
            return

        self.print_line(f"> {command}")

        self.input.clear()

        if command == "exit":
            self.close()
            return

        elif command == "help":
            self.print_line("Available commands: help, clear, exit, ls, pwd, cd, cat, touch, mkdir, delete, sha256, sha512, notepad")

        elif command == "ls":
            list_dir = os.listdir(self.cwd)

            for elem in list_dir:
                if os.path.isdir(elem):
                    self.print_line(f"{elem:<30} - directory")
                else:
                    self.print_line(f"{elem:<30} - {os.path.getsize(os.path.join(self.cwd, elem))} bytes")

        elif command == "pwd":
            self.print_line(f"path: {self.cwd}")

        elif command.startswith("mkdir"):
            args = command[6:].strip()

            os.mkdir(os.path.join(self.cwd, args))
            self.print_line(f"Directory created -> {args}")

        elif command.startswith("cd"):
            args = command[3:].strip()
            # self.print_line(f"{args}")
            new_path = os.path.abspath(
                os.path.join(self.cwd, args)
            )
            self.print_line(f"Changed path > {new_path}")

            if os.path.isdir(new_path):
                self.cwd = new_path
            else:
                self.print_line("No such directory.")

            # try:
            #     os.chdir(args)
            # except FileNotFoundError:
            #     self.print_line("No such file or directory.")
            # except FileExistsError:
            #     self.print_line("Target file/directory already satisfied.")
            # except NotADirectoryError:
            #     self.print_line("Error: Target file is not a directory.")
            # except PermissionError:
            #     self.print_line("Error: Permission denied.")
            # except Exception as e:
            #     self.print_line(f"Error: {str(e)}")

        elif command.startswith("cat"):
            args = command[4:].strip()
            filename = os.path.join(self.cwd, args)

            try:
                with open(filename, "r") as f:
                    self.print_line(f.read())
            except FileNotFoundError:
                self.print_line("No such file or directory.")
            except Exception as e:
                self.print_line(f"Error: {str(e)}")

        elif command.startswith("touch"):
            args = command[6:].strip()
            target = os.path.join(self.cwd, args)

            try:
                with open(target, "w") as f: pass
            except FileExistsError:
                self.print_line(f"Error: File {args} already exists.")
            except Exception as e:
                self.print_line(f"Error: {str(e)}")

        elif command.startswith("delete"):
            args = command[7:].strip()
            path = os.path.join(self.cwd, args)

            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    os.rmdir(path)
                else:
                    self.print_line("Error: No such file or directory.")
            except Exception as e:
                self.print_line(f"Error: {str(e)}")

        elif command.startswith("sha256"):
            filename = os.path.join(self.cwd, command[7:].strip())

            try:
                with open(filename, "r") as f:
                    content = f.read()
                    self.print_line(f"SHA-256 hash of {filename} -> {hashlib.sha256(content.encode()).hexdigest()}")
            except FileNotFoundError:
                self.print_line("Error: No such file or directory.")
            except Exception as e:
                self.print_line(f"Error: {str(e)}")

        elif command.startswith("sha512"):
            filename = os.path.join(self.cwd, command[7:].strip())

            try:
                with open(filename, "r") as f:
                    content = f.read()
                    self.print_line(f"SHA-512 hash of {filename} -> {hashlib.sha512(content.encode()).hexdigest()}")
            except FileNotFoundError:
                self.print_line("Error: No such file or directory.")
            except Exception as e:
                self.print_line(f"Error: {str(e)}")

        elif command.startswith("notepad"):
            filename = (self.cwd, command[8:].strip())
            try:
                from qjr_notepad import create_notepad

                editor = create_notepad(self)
                editor.load_file(filename)
                editor.show()

            except FileNotFoundError:
                self.print_line("QJRnotepad Error: No such file or directory.")

            except Exception as e:
                self.print_line(f"QJRnotepad Error: {str(e)}")


        elif command.lower() == "clear":
            self.clear_terminal()
            return

        else:
            self.print_line(f"Unknown command -> {command}")

        # # macOS / Linux
        #
        # if os.name == "posix":
        #
        #     self.process.start(
        #         "/bin/bash",
        #         ["-c", command]
        #     )
        #
        # # Windows
        #
        # else:
        #
        #     self.process.start(
        #         "cmd.exe",
        #         ["/c", command]
        #     )

    # ========================================
    # STDOUT
    # ========================================

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode(errors="ignore")
        self.print_line(text)

    # ========================================
    # STDERR
    # ========================================

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        text = bytes(data).decode(errors="ignore")
        self.print_line(text)

    # ========================================
    # CLEAR
    # ========================================

    def clear_terminal(self):
        self.output.clear()

    # ========================================
    # STOP PROCESS
    # ========================================

    def stop_process(self):
        if self.process.state() != QProcess.NotRunning:
            if self.current_shell == "/usr/bin/python3":
                self.process.write(b"exit()\n")
                if not self.process.waitForFinished(500):
                    self.process.kill()
            else:
                self.process.kill()

            self.print_line("[Process terminated]")

    # ========================================
    # CLOSE EVENT
    # ========================================

    def closeEvent(self, event):
        global _terminal_instance

        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.process.waitForFinished(500)

        _terminal_instance = None
        super().closeEvent(event)


# ============================================
# OPEN FUNCTION
# ============================================

# def open_term_console(parent=None):
#
#     global _terminal_instance
#
#     if _terminal_instance is None or not _terminal_instance.isVisible():
#         try:
#             _terminal_instance.show
#         except RuntimeError:
#             _terminal_instance = None
#
#     if _terminal_instance is None:
#         _terminal_instance = QJRTerminal(parent)
#
#     _terminal_instance.show()
#     _terminal_instance.raise_()
#     _terminal_instance.activateWindow()
#
#     return _terminal_instance

def open_term_console(parent=None):
    global _terminal_instance

    if _terminal_instance is not None:
        try:
            _terminal_instance.show()
            _terminal_instance.raise_()
            _terminal_instance.activateWindow()
            return _terminal_instance
        except RuntimeError:
            # C++-об'єкт уже видалений
            _terminal_instance = None

    _terminal_instance = QJRTerminal(parent)
    _terminal_instance.show()
    _terminal_instance.raise_()
    _terminal_instance.activateWindow()

    return _terminal_instance