import time
from pynput.keyboard import Controller
from AppKit import NSWorkspace, NSApplicationActivateIgnoringOtherApps

_keyboard = Controller()

# Bundle IDs de terminales conocidos — si la app capturada es una de estas,
# no intentamos activarla (el usuario ya ha cambiado de foco para cuando pegamos)
_TERMINAL_BUNDLES = {
    "com.mitchellh.ghostty",
    "com.apple.Terminal",
    "com.googlecode.iterm2",
    "dev.warp.Warp-Stable",
    "net.kovidgoyal.kitty",
}


def get_active_app():
    """Devuelve la app activa. Espera un tick para que macOS se estabilice tras el keydown."""
    time.sleep(0.05)
    return NSWorkspace.sharedWorkspace().frontmostApplication()


def paste_text(text: str, target_app=None):
    app = NSWorkspace.sharedWorkspace().frontmostApplication()

    if target_app is not None:
        bundle = target_app.bundleIdentifier() or ""
        is_terminal = bundle in _TERMINAL_BUNDLES

        if not is_terminal:
            # La app capturada no es un terminal: restaurar foco
            target_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            time.sleep(0.1)
        else:
            # Era un terminal: usar la app que tenga el foco ahora mismo
            print(f"[paster] Terminal detectado al pulsar — pegando en app actual: {app.localizedName()}")

    _keyboard.type(text)
