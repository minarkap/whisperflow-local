import time
from pynput.keyboard import Controller
from AppKit import NSWorkspace, NSApplicationActivateIgnoringOtherApps

_keyboard = Controller()


def get_active_app():
    return NSWorkspace.sharedWorkspace().frontmostApplication()


def paste_text(text: str, target_app=None):
    if target_app is not None:
        target_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        time.sleep(0.1)

    _keyboard.type(text)
