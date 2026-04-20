import threading
from typing import Callable
from pynput import keyboard


# Mapeo de nombres de config a teclas pynput
_MODIFIER_MAP = {
    "ctrl":  {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "alt":   {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r},
    "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
    "cmd":   {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
}

_KEY_MAP = {
    "space":   keyboard.Key.space,
    "tab":     keyboard.Key.tab,
    "enter":   keyboard.Key.enter,
    "alt_r":   keyboard.Key.alt_r,
    "alt_l":   keyboard.Key.alt_l,
    "ctrl_r":  keyboard.Key.ctrl_r,
    "ctrl_l":  keyboard.Key.ctrl_l,
    "shift_r": keyboard.Key.shift_r,
    "cmd_r":   keyboard.Key.cmd_r,
}

# pynput en macOS a veces entrega el release de una modifier como la variante
# genérica (Key.alt en lugar de Key.alt_l). Este mapa permite detectarlo.
_KEY_ALIASES: dict = {
    keyboard.Key.alt_l:   {keyboard.Key.alt_l,   keyboard.Key.alt},
    keyboard.Key.alt_r:   {keyboard.Key.alt_r,   keyboard.Key.alt},
    keyboard.Key.ctrl_l:  {keyboard.Key.ctrl_l,  keyboard.Key.ctrl},
    keyboard.Key.ctrl_r:  {keyboard.Key.ctrl_r,  keyboard.Key.ctrl},
    keyboard.Key.shift_l: {keyboard.Key.shift_l, keyboard.Key.shift},
    keyboard.Key.shift_r: {keyboard.Key.shift_r, keyboard.Key.shift},
    keyboard.Key.cmd_l:   {keyboard.Key.cmd_l,   keyboard.Key.cmd},
    keyboard.Key.cmd_r:   {keyboard.Key.cmd_r,   keyboard.Key.cmd},
}


def _parse_key(key_str: str):
    return _KEY_MAP.get(key_str.lower(), keyboard.KeyCode.from_char(key_str))


class HotkeyListener:
    def __init__(
        self,
        modifiers: list[str],
        key: str,
        on_press: Callable,
        on_release: Callable,
    ):
        self._modifier_sets = [_MODIFIER_MAP[m] for m in modifiers]
        self._trigger_key = _parse_key(key)
        self._on_press_cb = on_press
        self._on_release_cb = on_release

        self._held: set = set()
        self._held_lock = threading.Lock()
        self._active = False
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_key_down,
            on_release=self._on_key_up,
        )
        try:
            self._listener.start()
        except Exception as e:
            raise RuntimeError(
                f"No se pudo iniciar el listener de teclado: {e}\n"
                "Asegúrate de que la app tiene permisos de Accesibilidad en Preferencias del Sistema."
            ) from e

    def stop(self):
        if self._listener:
            self._listener.stop()

    # ------------------------------------------------------------------

    def _modifiers_held(self) -> bool:
        # Sin modificadores configurados → solo la tecla trigger
        if not self._modifier_sets:
            return True
        with self._held_lock:
            held_copy = set(self._held)
        return all(
            any(k in held_copy for k in mod_set)
            for mod_set in self._modifier_sets
        )

    def _on_key_down(self, key):
        with self._held_lock:
            self._held.add(key)
        mods_held = self._modifiers_held()
        with self._lock:
            if not self._active and self._is_trigger(key) and mods_held:
                self._active = True
                self._on_press_cb()

    def _on_key_up(self, key):
        with self._held_lock:
            self._held.discard(key)
        with self._lock:
            if self._active and self._is_trigger(key):
                self._active = False
                self._on_release_cb()

    def _is_trigger(self, key) -> bool:
        if isinstance(self._trigger_key, keyboard.Key):
            aliases = _KEY_ALIASES.get(self._trigger_key, {self._trigger_key})
            return key in aliases
        if isinstance(key, keyboard.KeyCode) and isinstance(self._trigger_key, keyboard.KeyCode):
            return key.char == self._trigger_key.char
        return False
