import builtins
import ctypes
import signal
import sys
import threading
import time
import tomllib
from datetime import datetime
from enum import Enum, auto
from pathlib import Path

import numpy as np

# ── Detección de estado físico de tecla (macOS CoreGraphics) ────────────────
# Permite detectar releases perdidos consultando el hardware directamente,
# sin depender de los eventos de pynput que el OS puede descartar.

try:
    _cg = ctypes.cdll.LoadLibrary(
        "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
    )
    _cg.CGEventSourceKeyState.argtypes = [ctypes.c_int, ctypes.c_uint16]
    _cg.CGEventSourceKeyState.restype  = ctypes.c_bool
    _CG_AVAILABLE = True
except OSError:
    _CG_AVAILABLE = False

_HID_STATE = 1  # kCGEventSourceStateHIDSystemState

_MACOS_KEYCODES: dict[str, int] = {
    "alt_l":   58, "alt_r":   61,
    "ctrl_l":  59, "ctrl_r":  62,
    "shift_l": 56, "shift_r": 60,
    "cmd_l":   55, "cmd_r":   54,
    "space":   49, "tab":     48, "enter": 36,
}

def _key_is_held(key_name: str) -> bool:
    """Devuelve True si la tecla está físicamente pulsada según el HW."""
    if not _CG_AVAILABLE:
        return True
    keycode = _MACOS_KEYCODES.get(key_name.lower())
    if keycode is None:
        return True  # tecla desconocida → no interferir
    return bool(_cg.CGEventSourceKeyState(_HID_STATE, keycode))

# Añade timestamp y flush automático a todos los print
_orig_print = builtins.print
def _ts_print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    _orig_print(f"[{datetime.now().strftime('%H:%M:%S')}]", *args, **kwargs)
builtins.print = _ts_print

from hotkey import HotkeyListener
from recorder import Recorder
from transcriber import Transcriber
from paster import paste_text, get_active_app
from formatter import format_text


# ── Estado de la máquina ────────────────────────────────────────────────────

class State(Enum):
    IDLE        = auto()
    RECORDING   = auto()
    TRANSCRIBING = auto()


# ── Beep ────────────────────────────────────────────────────────────────────

_BEEP_SR = 44100

def _make_beep(frequency: int, duration: float) -> "np.ndarray":
    n = int(_BEEP_SR * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    return (0.4 * np.sin(2 * np.pi * frequency * t) * np.exp(-5 * t / duration)).astype(np.float32)

# Pre-generar ambos pitidos al arrancar para que la reproducción sea instantánea
_BEEP_START = _make_beep(880, 0.06)
_BEEP_STOP  = _make_beep(440, 0.06)

def beep(wave: "np.ndarray"):
    import sounddevice as sd
    sd.play(wave, samplerate=_BEEP_SR)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    config_path = Path(__file__).parent.parent / "config.toml"
    try:
        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)
    except FileNotFoundError:
        print(f"Error: no se encontró config.toml en {config_path}")
        sys.exit(1)
    except tomllib.TOMLDecodeError as e:
        print(f"Error en config.toml: {e}")
        sys.exit(1)

    audio_cfg    = cfg["audio"]
    model_cfg    = cfg["model"]
    hotkey_cfg   = cfg["hotkey"]
    feedback_cfg = cfg.get("feedback", {})

    recorder = Recorder(
        sample_rate=audio_cfg["sample_rate"],
        channels=audio_cfg["channels"],
        device=audio_cfg.get("device"),
    )

    transcriber = Transcriber(
        engine="whisper",
        model_repo=model_cfg["whisper_repo"],
        language=model_cfg.get("language") or None,
    )
    try:
        transcriber.load()
    except Exception as e:
        print(f"Error cargando el modelo: {e}")
        sys.exit(1)

    state      = State.IDLE
    state_lock = threading.Lock()
    target_app = None

    def _set_idle():
        nonlocal state
        with state_lock:
            state = State.IDLE

    def _finish_recording():
        nonlocal state
        with state_lock:
            if state != State.RECORDING:
                return
            state = State.TRANSCRIBING

        if feedback_cfg.get("stop_sound", True):
            beep(_BEEP_STOP)

        audio = recorder.stop()
        secs = len(audio) / audio_cfg["sample_rate"]
        print(f"■ Grabación parada ({secs:.1f}s). Transcribiendo...")

        if secs < 1.0:
            print("Audio demasiado corto, ignorando.")
            _set_idle()
            return

        app = target_app

        def _work():
            try:
                text = transcriber.transcribe(audio, sample_rate=audio_cfg["sample_rate"])
                if text:
                    if feedback_cfg.get("format_lists", True):
                        text = format_text(text)
                    paste_text(text, target_app=app)
                    print(f'✓ Pegado: "{text}"')
                else:
                    print("Sin transcripción.")
            except Exception as e:
                print(f"Error en transcripción: {e}")
            finally:
                _set_idle()

        threading.Thread(target=_work, daemon=True).start()

    def _set_target_app():
        nonlocal target_app
        target_app = get_active_app()

    def on_press():
        nonlocal state, target_app
        with state_lock:
            if state != State.IDLE:
                return
            state = State.RECORDING
        # Iniciar grabación primero para no perder el inicio del audio
        recorder.start()
        if feedback_cfg.get("start_sound", True):
            beep(_BEEP_START)
        print("● Grabando...")
        # Detectar app activa en background (solo se necesita al pegar, no ahora)
        target_app = None
        threading.Thread(target=lambda: _set_target_app(), daemon=True).start()

        # Watchdog de hardware: comprueba el estado físico de la tecla
        # cada 200ms. Si el OS perdió el evento de release, lo detecta aquí.
        def _hw_watchdog():
            time.sleep(0.5)  # margen inicial para que el press se registre
            while True:
                with state_lock:
                    if state != State.RECORDING:
                        break
                if not _key_is_held(hotkey_cfg["key"]):
                    print("⚠ Release de tecla no recibido, recuperando.")
                    _finish_recording()
                    break
                time.sleep(0.2)

        threading.Thread(target=_hw_watchdog, daemon=True).start()

    def on_release():
        _finish_recording()

    listener = HotkeyListener(
        modifiers=hotkey_cfg["modifiers"],
        key=hotkey_cfg["key"],
        on_press=on_press,
        on_release=on_release,
    )

    stop_event = threading.Event()

    def _handle_sigint(sig, frame):
        print("\nSaliendo...")
        listener.stop()
        try:
            recorder.stop()
        except Exception:
            pass
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_sigint)

    mods     = hotkey_cfg["modifiers"]
    key_name = hotkey_cfg["key"]
    atajo    = " + ".join(mods + [key_name]) if mods else key_name

    print("WhisperFlow Local arrancado.")
    print(f"Atajo: {atajo}  |  Ctrl+C para salir.\n")

    try:
        listener.start()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    stop_event.wait()
    sys.exit(0)


if __name__ == "__main__":
    main()
