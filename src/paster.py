import time
from pynput.keyboard import Controller, Key
from AppKit import NSWorkspace, NSPasteboard

_keyboard = Controller()
_PBOARD_TYPE = "public.utf8-plain-text"


def get_active_app():
    """Devuelve la app activa al pulsar la tecla."""
    time.sleep(0.05)
    return NSWorkspace.sharedWorkspace().frontmostApplication()


def paste_text(text: str, target_app=None):
    """Pega el texto vía portapapeles + Cmd+V (instantáneo para cualquier longitud).

    Guarda el contenido anterior del portapapeles y lo restaura tras el pegado,
    para que el usuario no pierda lo que tuviera copiado.
    """
    current = NSWorkspace.sharedWorkspace().frontmostApplication()
    pressed_in = target_app.localizedName() if target_app else "?"
    print(f"[paster] Pulsado en: {pressed_in} → Pegando en: {current.localizedName()}")

    pb = NSPasteboard.generalPasteboard()
    old = pb.stringForType_(_PBOARD_TYPE) or ""

    pb.clearContents()
    pb.setString_forType_(text, _PBOARD_TYPE)

    _keyboard.press(Key.cmd)
    _keyboard.press('v')
    _keyboard.release('v')
    _keyboard.release(Key.cmd)

    # Espera a que la app procese el pegado antes de restaurar el portapapeles
    time.sleep(0.15)
    pb.clearContents()
    pb.setString_forType_(old, _PBOARD_TYPE)
