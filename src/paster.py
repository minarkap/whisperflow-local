import subprocess
import pyperclip


def paste_text(text: str):
    # Guardar clipboard original para restaurarlo después
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""

    pyperclip.copy(text)

    # Cmd+V via AppleScript — funciona en cualquier app macOS
    script = 'tell application "System Events" to keystroke "v" using {command down}'
    subprocess.run(["osascript", "-e", script], check=True)

    # Restaurar clipboard original (sin bloquear el flujo si falla)
    try:
        pyperclip.copy(original)
    except Exception:
        pass
