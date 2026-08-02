import io
import json
from pathlib import Path

from google import genai
from google.genai import types

from huggingface_hub import InferenceClient
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QTextEdit,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QTabWidget,
    QWidget,
    QFileDialog,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


# PATHS

# Directory, where is this Python-file.
# Thanks to this, the program does not depend on the current working directory.
BASE_DIR = Path(__file__).resolve().parent

CONFIG_DIR = BASE_DIR / "config"
AI_CONFIG_FILE = CONFIG_DIR / "ai.json"

USER_DIR = BASE_DIR / "user"
IMAGE_DIR = USER_DIR / "images"


# CONFIG

DEFAULT_AI_CONFIG = {
    "gemini": {
        "api_key": ""
    },
    "huggingface": {
        "token": ""
    }
}


def load_ai_config():
    """
    Loading AI configuration from config/ai.json.

    If the file doesn't exist — create it
    with empty API keys.
    """

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not AI_CONFIG_FILE.exists():
        save_ai_config(DEFAULT_AI_CONFIG)
        return DEFAULT_AI_CONFIG.copy()

    try:
        with AI_CONFIG_FILE.open("r", encoding="utf-8") as file:
            config = json.load(file)

    except (json.JSONDecodeError, OSError):
        config = DEFAULT_AI_CONFIG.copy()

    # Захист від неповного / пошкодженого config
    if not isinstance(config, dict):
        config = {}

    if not isinstance(config.get("gemini"), dict):
        config["gemini"] = {}

    if not isinstance(config.get("huggingface"), dict):
        config["huggingface"] = {}

    config["gemini"].setdefault("api_key", "")
    config["huggingface"].setdefault("token", "")

    return config


def save_ai_config(config):
    """
    Saves AI configuration to config/ai.json.
    """

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    with AI_CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            config,
            file,
            indent=4,
            ensure_ascii=False
        )


# Loading a config
ai_config = load_ai_config()


# GEMINI

API_KEY = ai_config["gemini"].get("api_key", "").strip()

client = None
chat = None


def create_gemini_client(api_key):
    """
    Creates Gemini and chat
    """

    if not api_key:
        return None, None

    new_client = genai.Client(api_key=api_key)

    new_chat = new_client.chats.create(
        model="gemini-3.1-flash-lite-preview",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a useful assistant. "
                "Answer clearly and understandably."
            ),
            thinking_config=types.ThinkingConfig(
                thinking_level="low"
            ),
            max_output_tokens=2048,
        ),
    )

    return new_client, new_chat


# Automaticly connecting Gemini
# if key is already at ai/key.json.
if API_KEY:
    try:
        client, chat = create_gemini_client(API_KEY)
    except Exception:
        client = None
        chat = None


# HUGGING FACE

HF_TOKEN = ai_config["huggingface"].get("token", "").strip()

hf_client = None

if HF_TOKEN:
    try:
        hf_client = InferenceClient(
            api_key=HF_TOKEN
        )
    except Exception:
        hf_client = None


# IMAGE GENERATION

def generate_image_bytes(prompt: str) -> bytes:
    """
    Generates image through Hugging Face FLUX
    and returns PNG bytes.
    """

    if hf_client is None:
        raise RuntimeError(
            "Hugging Face token is not configured."
        )

    image = hf_client.text_to_image(
        prompt=prompt,
        model="black-forest-labs/FLUX.1-schnell"
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()


# UI CLASS

class GeminiDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("QJR AI System")
        self.resize(750, 600)

        self.image_counter = self.find_next_image_number()

        self.current_image = None

        self.setStyleSheet("""
            QDialog {
                background-color: #15151f;
            }

            QLabel {
                color: white;
            }

            QTextEdit {
                background-color: #222236;
                color: white;
                border-radius: 10px;
                padding: 8px;
            }

            QLineEdit {
                background-color: #222236;
                color: white;
                border-radius: 8px;
                padding: 6px;
            }

            QPushButton {
                background-color: #c2185b;
                color: white;
                border-radius: 10px;
                padding: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #e91e63;
            }

            QTabWidget::pane {
                border: 0;
            }

            QTabBar::tab {
                background-color: #222236;
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
            }

            QTabBar::tab:selected {
                background-color: #c2185b;
            }
        """)

        self.init_ui()

    # UI SETUP

    def init_ui(self):

        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        self.chat_tab = QWidget()
        self.image_tab = QWidget()

        self.init_chat_tab()
        self.init_image_tab()

        self.tabs.addTab(
            self.chat_tab,
            "Chat"
        )

        self.tabs.addTab(
            self.image_tab,
            "Image Gen"
        )

        # API Settings
        # Gemini button (left)
        self.api_key_btn = QPushButton(
            "API Key"
        )

        self.api_key_btn.clicked.connect(
            self.change_api_key
        )

        # Hugging Face button (right)
        self.hf_token_btn = QPushButton(
            "HF Token"
        )

        self.hf_token_btn.clicked.connect(
            self.change_hf_token
        )

        # Adding to the layout manager

        layout.addWidget(
            self.api_key_btn
        )

        layout.addWidget(
            self.hf_token_btn
        )

        layout.addWidget(
            self.tabs
        )

        self.setLayout(layout)

    # CHAT TAB

    def init_chat_tab(self):

        layout = QVBoxLayout()

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)

        self.input_field = QLineEdit()

        self.input_field.setPlaceholderText(
            "Enter a message..."
        )

        btns = QHBoxLayout()

        self.send_btn = QPushButton(
            "Send"
        )

        self.clear_btn = QPushButton(
            "Clear"
        )

        btns.addWidget(
            self.send_btn
        )

        btns.addWidget(
            self.clear_btn
        )

        layout.addWidget(
            self.chat_view
        )

        layout.addWidget(
            self.input_field
        )

        layout.addLayout(
            btns
        )

        self.chat_tab.setLayout(
            layout
        )

        self.send_btn.clicked.connect(
            self.send_message
        )

        self.input_field.returnPressed.connect(
            self.send_message
        )

        self.clear_btn.clicked.connect(
            self.chat_view.clear
        )

    # SEND MESSAGE

    def send_message(self):

        global chat

        text = self.input_field.text().strip()

        if not text:
            return

        if chat is None:

            QMessageBox.warning(
                self,
                "Gemini",
                "Gemini API key is not configured.\n\n"
                "Click 'API Key' and enter your key."
            )

            return

        self.chat_view.append(
            f"You: {text}"
        )

        self.input_field.clear()

        try:

            response = chat.send_message(
                text
            )

            self.chat_view.append(
                f"Gemini: {response.text}\n"
            )

        except Exception as e:

            self.chat_view.append(
                f"[Error]: {e}\n"
            )

    # IMAGE TAB

    def init_image_tab(self):

        layout = QVBoxLayout()

        self.prompt_input = QLineEdit()

        self.prompt_input.setPlaceholderText(
            "Prompt for image generation..."
        )

        self.generate_btn = QPushButton(
            "Generate"
        )

        self.save_btn = QPushButton(
            "Save"
        )

        self.image_label = QLabel(
            "Image will appear here..."
        )

        self.image_label.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            self.prompt_input
        )

        layout.addWidget(
            self.generate_btn
        )

        layout.addWidget(
            self.image_label
        )

        layout.addWidget(
            self.save_btn
        )

        self.image_tab.setLayout(
            layout
        )

        self.generate_btn.clicked.connect(
            self.generate_image_ui
        )

        self.save_btn.clicked.connect(
            self.save_image
        )

    # IMAGE GENERATION

    def generate_image_ui(self):

        prompt = self.prompt_input.text().strip()

        if not prompt:
            return

        try:

            # Створюємо папку автоматично
            IMAGE_DIR.mkdir(
                parents=True,
                exist_ok=True
            )

            img_bytes = generate_image_bytes(
                prompt
            )

            filename = (
                IMAGE_DIR /
                f"image_{self.image_counter}.png"
            )

            self.image_counter += 1

            with filename.open(
                "wb"
            ) as file:

                file.write(
                    img_bytes
                )

            self.current_image = filename

            pixmap = QPixmap(
                str(filename)
            )

            self.image_label.setPixmap(
                pixmap.scaled(
                    450,
                    450,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )

        except Exception as e:

            self.image_label.setText(
                f"Error: {e}"
            )

    # SAVE IMAGE

    def save_image(self):

        if self.current_image is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            str(self.current_image),
            "Images (*.png *.jpg *.jpeg)"
        )

        if not path:
            return

        try:

            with open(
                self.current_image,
                "rb"
            ) as src:

                with open(
                    path,
                    "wb"
                ) as dst:

                    dst.write(
                        src.read()
                    )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Save Error",
                str(e)
            )

    # API KEY

    def change_api_key(self):

        global API_KEY
        global client
        global chat

        key, ok = QInputDialog.getText(
            self,
            "Gemini API Key",
            "Enter your Gemini API key:",
            QLineEdit.Password,
            API_KEY
        )

        if not ok:
            return

        key = key.strip()

        if not key:
            QMessageBox.warning(
                self,
                "Gemini",
                "API key cannot be empty."
            )

            return

        try:

            new_client, new_chat = (
                create_gemini_client(key)
            )

            # if everything is successful
            API_KEY = key
            client = new_client
            chat = new_chat

            ai_config["gemini"]["api_key"] = (
                API_KEY
            )

            save_ai_config(
                ai_config
            )

            QMessageBox.information(
                self,
                "Gemini",
                "Gemini API key saved successfully."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Gemini Error",
                f"Failed to configure Gemini:\n\n{e}"
            )

    def change_hf_token(self):

        global HF_TOKEN
        global hf_client

        key, ok = QInputDialog.getText(
            self,
            "Hugging Face (Flux model) Token",
            "Enter your Hugging Face token:",
            QLineEdit.Password,
            HF_TOKEN
        )

        if not ok:
            return

        key = key.strip()

        if not key:
            QMessageBox.warning(
                self,
                "Hugging Face (Flux model) token",
                "HF token cannot be empty."
            )
            return

        try:
            new_hf_client = InferenceClient(
                api_key=key
            )

            HF_TOKEN = key
            hf_client = new_hf_client

            ai_config["huggingface"]["token"] = HF_TOKEN
            save_ai_config(ai_config)

            QMessageBox.information(
                self,
                "Hugging Face (Flux model) token",
                "Hugging Face (Flux model) token saved successfully."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Hugging Face (Flux model) Error",
                f"Failed to configure Hugging Face (Flux model):\n\n{e}"
            )

    # IMAGE COUNTER

    @staticmethod
    def find_next_image_number():
        if not IMAGE_DIR.exists():
            return 1

        numbers = []

        for file in IMAGE_DIR.glob(
            "image_*.png"
        ):
            try:
                number = int(
                    file.stem.split("_")[-1]
                )

                numbers.append(
                    number
                )

            except ValueError:
                pass

        if not numbers:
            return 1

        return max(numbers) + 1


# RUN

if __name__ == "__main__":
    app = QApplication([])
    window = GeminiDialog()
    window.show()
    app.exec()