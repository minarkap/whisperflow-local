import sys
import threading
import tomllib
from pathlib import Path

from hotkey import HotkeyListener
from recorder import Recorder
from transcriber import Transcriber
from paster import paste_text, get_active_app


def beep(frequency: int = 1000, duration: float = 0.08):
    """Beep usando afplay con un archivo de audio temporal (se borra al terminar)."""
    import subprocess, struct, wave, tempfile, os, math
    n = int(44100 * duration)
    samples = [int(32767 * math.sin(2 * math.pi * frequency * i / 44100)) for i in range(n)]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(struct.pack(f"<{n}h", *samples))

    def play_and_delete():
        subprocess.run(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.unlink(path)

    import threading
    threading.Thread(target=play_and_delete, daemon=True).start()


def load_config(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def main():
    config_path = Path(__file__).parent.parent / "config.toml"
    cfg = load_config(config_path)

    audio_cfg   = cfg["audio"]
    model_cfg   = cfg["model"]
    hotkey_cfg  = cfg["hotkey"]
    feedback_cfg = cfg.get("feedback", {})

    recorder = Recorder(
        sample_rate=audio_cfg["sample_rate"],
        channels=audio_cfg["channels"],
        device=audio_cfg.get("device"),
    )

    engine = model_cfg.get("engine", "voxtral-mini-3b")
    if engine == "voxtral-mini-3b":
        model_repo = model_cfg["voxtral_repo"]
    else:
        model_repo = model_cfg["whisper_repo"]

    transcriber = Transcriber(
        model_repo=model_repo,
        language=model_cfg.get("language"),
    )

    # Cargar modelo al arrancar (no al primer uso)
    transcriber.load()

    _lock = threading.Lock()
    _busy = False
    _target_app = None

    def on_press():
        nonlocal _busy, _target_app
        with _lock:
            if _busy:
                return
        # Capturar la app con foco ANTES de que el usuario empiece a hablar
        _target_app = get_active_app()
        if feedback_cfg.get("start_sound", True):
            beep(880)
        recorder.start()
        print("● Grabando...")

    def on_release():
        nonlocal _busy
        with _lock:
            if _busy:
                return
            _busy = True

        if feedback_cfg.get("stop_sound", True):
            beep(440)

        audio = recorder.stop()
        print(f"■ Grabación parada ({len(audio)/audio_cfg['sample_rate']:.1f}s). Transcribiendo...")

        if len(audio) < audio_cfg["sample_rate"] * 0.3:
            print("Audio demasiado corto, ignorando.")
            with _lock:
                _busy = False
            return

        target = _target_app

        def transcribe_and_paste():
            nonlocal _busy
            try:
                text = transcriber.transcribe(audio, sample_rate=audio_cfg["sample_rate"])
                if text:
                    paste_text(text, target_app=target)
                    print(f'✓ Pegado: "{text}"')
                else:
                    print("Sin transcripción.")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                with _lock:
                    _busy = False

        threading.Thread(target=transcribe_and_paste, daemon=True).start()

    listener = HotkeyListener(
        modifiers=hotkey_cfg["modifiers"],
        key=hotkey_cfg["key"],
        on_press=on_press,
        on_release=on_release,
    )

    print("WhisperFlow Local arrancado.")
    mods = hotkey_cfg["modifiers"]
    key_name = hotkey_cfg["key"]
    atajo = " + ".join(mods + [key_name]) if mods else key_name
    print(f"Atajo: {atajo}")
    print("Ctrl+C para salir.\n")

    listener.start()

    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("\nSaliendo...")
        listener.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
