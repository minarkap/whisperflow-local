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
    "space": keyboard.Key.space,
    "tab":   keyboard.Key.tab,
    "enter": keyboard.Key.enter,
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
        self._active = False
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_key_down,
            on_release=self._on_key_up,
        )
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    # ------------------------------------------------------------------

    def _modifiers_held(self) -> bool:
        return all(
            any(k in self._held for k in mod_set)
            for mod_set in self._modifier_sets
        )

    def _on_key_down(self, key):
        self._held.add(key)
        with self._lock:
            if not self._active and self._is_trigger(key) and self._modifiers_held():
                self._active = True
                self._on_press_cb()

    def _on_key_up(self, key):
        self._held.discard(key)
        with self._lock:
            if self._active and self._is_trigger(key):
                self._active = False
                self._on_release_cb()

    def _is_trigger(self, key) -> bool:
        if isinstance(self._trigger_key, keyboard.Key):
            return key == self._trigger_key
        # KeyCode: comparar char
        if isinstance(key, keyboard.KeyCode) and isinstance(self._trigger_key, keyboard.KeyCode):
            return key.char == self._trigger_key.char
        return False
