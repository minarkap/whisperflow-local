# PRD — WhisperFlow Local

## Descripción
Herramienta de dictado por voz local para macOS. Mantén pulsado un atajo de teclado, habla, suelta, y el texto aparece donde está el cursor. Sin nube, sin créditos, sin suscripciones.

## Problema que resuelve
Sustituto local de WhisperFlow (SaaS) para no depender de créditos de pago. Toda la transcripción ocurre en el dispositivo usando Apple Silicon.

## Usuario final
Uso personal interno.

## Objetivos y métricas de éxito
- Latencia < 3 segundos desde que se suelta el botón hasta que el texto aparece (para frases de 10-15 segundos)
- Precisión comparable a Whisper medium/large
- 0 dependencias de red

## Casos de uso
1. Usuario mantiene pulsado el atajo mientras habla
2. Al soltar, el audio se transcribe localmente
3. El texto se pega automáticamente en el campo donde estaba el cursor

## Stack tecnológico

| Componente | Tecnología | Razón |
|---|---|---|
| Lenguaje | Python 3.12 | Stack habitual |
| Transcripción | `mlx-voxtral` + Voxtral Mini 3B | Mejor modelo local para español en 2026, Apache 2.0, MLX nativo M1, ~4% WER en FLEURS, supera a Whisper y GPT-4o mini en multilingüe |
| Grabación audio | `sounddevice` + `numpy` | Simple, fiable, bajo nivel |
| Hotkeys globales | `pynput` | Global hotkeys en macOS con Accessibility |
| Clipboard + paste | `pyperclip` + AppleScript | Paste nativo macOS más fiable que simulación de teclado |

## Atajo de teclado
**`Ctrl+Option+Space`** (⌃⌥Space) — push-to-talk, mantener pulsado

> No colisiona con Spotlight (⌘Space), Alfred (⌥Space), terminales ni IDEs. Configurable en `config.toml`.

## Requisitos funcionales
- [ ] Detectar pulsación global del atajo (aunque la app esté en background)
- [ ] Grabar audio del micrófono mientras se mantiene pulsado
- [ ] Transcribir con `mlx-whisper` al soltar
- [ ] Pegar texto en la posición del cursor activa
- [ ] Feedback auditivo (beep corto al empezar y al acabar)

## Requisitos no funcionales
- Funciona como proceso en background (daemon)
- No requiere interfaz gráfica
- Pide permisos de Accesibilidad y Micrófono al primer arranque
- Configurable mediante archivo `.env` o `config.toml`

## Fuera de scope (MVP)
- Interfaz gráfica / menubar icon
- Múltiples idiomas configurables (por defecto: autodetect)
- Historial de transcripciones
- Wake word ("Oye Whisper...")
- Integración con otras apps
