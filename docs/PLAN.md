# Plan de fases — WhisperFlow Local

## Fase 1: Setup y esqueleto [ ]
- [ ] Inicializar git + .gitignore
- [ ] Crear entorno virtual `.venv` con Python 3.12
- [ ] Instalar dependencias base (`mlx-whisper`, `sounddevice`, `pynput`, `pyperclip`, `numpy`, `tomllib`)
- [ ] Crear estructura de carpetas según arquitectura
- [ ] `config.toml` con valores por defecto
- [ ] `src/main.py` vacío que arranca sin errores
- **Criterio de éxito:** `python src/main.py` ejecuta sin errores

## Fase 2: Grabación de audio [ ]
- [ ] Implementar `src/recorder.py`
  - `start_recording()` — abre stream de sounddevice
  - `stop_recording()` → devuelve `numpy.ndarray` de audio a 16kHz
- [ ] Test manual: grabar 5s y guardar como `.wav` para verificar calidad
- **Criterio de éxito:** Audio grabado es limpio y a la frecuencia correcta (16kHz mono)

## Fase 3: Transcripción local [ ]
- [ ] Implementar `src/transcriber.py`
  - `transcribe(audio_array)` → `str`
  - Carga modelo `whisper-large-v3-turbo` (descarga en primer uso)
  - Autodetect de idioma
- [ ] Test manual: pasar audio de prueba y medir latencia
- **Criterio de éxito:** Transcripción correcta en < 3s para frases de ~10s

## Fase 4: Hotkey global [ ]
- [ ] Implementar `src/hotkey.py`
  - Listener global con `pynput`
  - Callbacks `on_press` / `on_release` para la combo configurada
  - Atajo configurable desde `config.toml`
- [ ] Test manual: verificar que captura el atajo en background (con otra app en foco)
- **Criterio de éxito:** Hotkey funciona con Terminal, Chrome, VSCode en foco

## Fase 5: Paste automático [ ]
- [ ] Implementar `src/paster.py`
  - `paste_text(text: str)` — copia al clipboard y simula Cmd+V via AppleScript
- [ ] Test manual: verificar que pega en distintas apps (TextEdit, Chrome, VSCode, terminal)
- **Criterio de éxito:** Texto aparece en el campo activo en todas las apps probadas

## Fase 6: Integración y pulido [ ]
- [ ] Conectar todo en `src/main.py`: hotkey → recorder → transcriber → paster
- [ ] Feedback auditivo (beep al empezar y al acabar con `afplay`)
- [ ] Manejo de errores: micrófono no disponible, modelo no descargado, etc.
- [ ] README con instrucciones de instalación y permisos necesarios
- **Criterio de éxito:** Flujo completo funciona de principio a fin 10 veces seguidas sin fallos

## Fase 7 (opcional, post-MVP): LaunchAgent [ ]
- [ ] Crear `.plist` para arrancar con el sistema
- [ ] Script de instalación `install.sh`
- **Criterio de éxito:** La herramienta arranca sola al iniciar sesión

---

## Estado actual
- [x] Entrevista inicial completada
- [x] Documentación aprobada
- [ ] Fase 1 pendiente de arrancar
