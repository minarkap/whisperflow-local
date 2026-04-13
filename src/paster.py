import time
import pyperclip
from pynput.keyboard import Controller, Key

_keyboard = Controller()


def paste_text(text: str):
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    pyperclip.copy(text)

    # Pequeña pausa para que el clipboard se asiente antes de pegar
    time.sleep(0.05)

    # Cmd+V via pynput — mismo proceso, mismo permiso de Accesibilidad
    with _keyboard.pressed(Key.cmd):
        _keyboard.press("v")
        _keyboard.release("v")

    time.sleep(0.05)

    try:
        pyperclip.copy(original)
    except Exception:
        pass
