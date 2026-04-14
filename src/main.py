import signal
import sys
import threading
import tomllib
from enum import Enum, auto
from pathlib import Path

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

def beep(frequency: int = 1000, duration: float = 0.06):
    import math, os, struct, subprocess, tempfile, wave
    n = int(44100 * duration)
    samples = [
        int(2600 * math.sin(2 * math.pi * frequency * i / 44100) * math.exp(-4 * i / n))
        for i in range(n)
    ]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    with wave.open(path, "w") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100)
        wf.writeframes(struct.pack(f"<{n}h", *samples))

    def _play():
        subprocess.run(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.unlink(path)

    threading.Thread(target=_play, daemon=True).start()


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    config_path = Path(__file__).parent.parent / "config.toml"
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

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
    transcriber.load()

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
            beep(440)

        audio = recorder.stop()
        secs = len(audio) / audio_cfg["sample_rate"]
        print(f"■ Grabación parada ({secs:.1f}s). Transcribiendo...")

        if secs < 0.3:
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

    def on_press():
        nonlocal state, target_app
        with state_lock:
            if state != State.IDLE:
                return
            state = State.RECORDING
        target_app = get_active_app()
        if feedback_cfg.get("start_sound", True):
            beep(880)
        recorder.start()
        print("● Grabando...")

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
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_sigint)

    mods     = hotkey_cfg["modifiers"]
    key_name = hotkey_cfg["key"]
    atajo    = " + ".join(mods + [key_name]) if mods else key_name

    print("WhisperFlow Local arrancado.")
    print(f"Atajo: {atajo}  |  Ctrl+C para salir.\n")

    listener.start()
    stop_event.wait()
    sys.exit(0)


if __name__ == "__main__":
    main()
