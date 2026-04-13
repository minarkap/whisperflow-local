import time
import pyperclip
from pynput.keyboard import Controller, Key
from AppKit import NSWorkspace

_keyboard = Controller()


def get_active_app():
    """Devuelve la app con foco en este momento."""
    return NSWorkspace.sharedWorkspace().frontmostApplication()


def paste_text(text: str, target_app=None):
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    pyperclip.copy(text)
    time.sleep(0.05)

    # Restaurar foco a la app que tenía el cursor antes de grabar
    if target_app is not None:
        target_app.activateWithOptions_(0)
        time.sleep(0.1)

    with _keyboard.pressed(Key.cmd):
        _keyboard.press("v")
        _keyboard.release("v")

    time.sleep(0.05)

    try:
        pyperclip.copy(original)
    except Exception:
        pass
