import time
from pynput.keyboard import Controller
from AppKit import NSWorkspace

_keyboard = Controller()


def get_active_app():
    """Devuelve la app con foco en este momento."""
    return NSWorkspace.sharedWorkspace().frontmostApplication()


def paste_text(text: str, target_app=None):
    # Restaurar foco a la app que tenía el cursor antes de grabar
    if target_app is not None:
        target_app.activateWithOptions_(0)
        time.sleep(0.15)

    # Escribir directamente en la app activa, sin tocar el portapapeles
    _keyboard.type(text)
