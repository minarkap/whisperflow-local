# Arquitectura — WhisperFlow Local

## Estructura de carpetas

```
whisperflow-local/
├── docs/
│   ├── PRD.md
│   ├── ARQUITECTURA.md
│   └── PLAN.md
├── src/
│   ├── main.py          # Punto de entrada, loop principal
│   ├── hotkey.py        # Listener global de teclado (pynput)
│   ├── recorder.py      # Grabación de audio (sounddevice)
│   ├── transcriber.py   # Transcripción (mlx-whisper)
│   └── paster.py        # Clipboard + paste (AppleScript)
├── config.toml          # Configuración: atajo, modelo, idioma
├── .env.example
├── .gitignore
├── README.md
├── CLAUDE.md
└── requirements.txt
```

## Diagrama de componentes

```
┌─────────────────────────────────────────────────────┐
│                    main.py (daemon)                  │
│                                                      │
│   ┌──────────┐    press    ┌──────────────────────┐ │
│   │ hotkey.py│ ──────────► │    recorder.py        │ │
│   │ (pynput) │    release  │  (sounddevice+numpy)  │ │
│   └──────────┘ ◄────────── └──────────┬───────────┘ │
│                                        │ audio[]     │
│                                        ▼             │
│                              ┌──────────────────┐   │
│                              │ transcriber.py   │   │
│                              │  (mlx-whisper)   │   │
│                              └────────┬─────────┘   │
│                                       │ text         │
│                                       ▼             │
│                              ┌──────────────────┐   │
│                              │   paster.py      │   │
│                              │ (pyperclip +     │   │
│                              │  AppleScript)    │   │
│                              └──────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## Flujo de datos principal

```
1. main.py arranca → carga config → inicializa hotkey listener
2. Usuario mantiene Ctrl+Shift+Space
   → hotkey.py dispara on_press → recorder.py empieza a capturar
3. Usuario suelta Ctrl+Shift+Space
   → hotkey.py dispara on_release → recorder.py para y devuelve audio (numpy array)
4. main.py pasa audio → transcriber.py
   → mlx-whisper procesa en Apple Silicon → devuelve string de texto
5. main.py pasa texto → paster.py
   → copia al clipboard → ejecuta AppleScript para Cmd+V
6. Texto aparece en la app activa donde estaba el cursor
```

## Decisiones técnicas

### ¿Por qué `mlx-whisper` y no `faster-whisper`?
`faster-whisper` usa CTranslate2 optimizado para CPU/CUDA. En Apple Silicon, `mlx-whisper` usa el framework MLX de Apple que aprovecha el Neural Engine y la memoria unificada del M1. Es notablemente más rápido en M-series.

### ¿Por qué AppleScript para pegar y no `pynput.keyboard.press('cmd+v')`?
`pynput` para simular teclado en macOS requiere permisos de Accesibilidad y a veces falla dependiendo de la app activa. AppleScript con `System Events` es más fiable para simular `Cmd+V` en cualquier app.

### ¿Por qué proceso daemon y no LaunchAgent?
Para el MVP, basta con ejecutar `python src/main.py` en background. En una fase posterior se puede empaquetar como LaunchAgent para que arranque con el sistema.

### Modelo de transcripción
- **Principal**: `mzbac/voxtral-mini-3b-4bit-mixed` vía `mlx-voxtral` — mejor modelo local para español en 2026 (~3.2 GB, ~4% WER en FLEURS, supera a Whisper y GPT-4o mini)
- **Fallback**: `mlx-community/whisper-large-v3-mlx` vía `mlx-whisper` — por si acaso, configurable en `config.toml`

## Permisos macOS necesarios
1. **Micrófono** — para grabar audio
2. **Accesibilidad** — para que `pynput` capture hotkeys globales fuera del foco
