import time
from pynput.keyboard import Controller
from AppKit import NSWorkspace, NSApplicationActivateIgnoringOtherApps

_keyboard = Controller()


def get_active_app():
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    print(f"[paster] App capturada: {app.localizedName()}")
    return app


def paste_text(text: str, target_app=None):
    if target_app is not None:
        print(f"[paster] Activando: {target_app.localizedName()}")
        target_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        time.sleep(0.2)

    _keyboard.type(text)
