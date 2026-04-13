# WhisperFlow Local

Dictado por voz 100% local para macOS Apple Silicon. Mantén pulsada una tecla, habla, suéltala — el texto aparece donde tengas el cursor.

Sin APIs de pago. Sin nube. Sin historial de portapapeles contaminado.

## Cómo funciona

1. Mantienes pulsada `alt_r` (Option derecha)
2. Hablas
3. Sueltas la tecla
4. El texto transcrito aparece en la app que tengas activa

El audio nunca sale de tu máquina. La transcripción corre sobre el chip Neural Engine del M1/M2/M3 vía MLX.

## Requisitos

- macOS con Apple Silicon (M1 / M2 / M3)
- Python 3.12 (recomendado via [pyenv](https://github.com/pyenv/pyenv))
- ~500 MB de espacio para el modelo Whisper

## Instalación

```bash
# 1. Clona el repo
git clone git@github.com:minarkap/whisperflow-local.git
cd whisperflow-local

# 2. Crea el entorno virtual e instala dependencias
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Instala como servicio de fondo (arranca solo al iniciar sesión)
bash install.sh
```

El modelo (~450 MB) se descarga automáticamente en el primer uso desde Hugging Face.

## Permisos de macOS

Al arrancar por primera vez, macOS pedirá dos permisos para `python3.12`:

| Permiso | Para qué |
|---|---|
| **Monitorización de dispositivos de entrada** | Detectar la tecla `alt_r` globalmente |
| **Accesibilidad** | Simular pulsaciones de teclado para pegar el texto |

Ajustes del sistema → Privacidad y seguridad → (cada sección) → añadir `python3.12`.

Sin estos permisos el hotkey no funciona o el texto no se pega.

## Configuración

Todo en `config.toml`:

```toml
[hotkey]
modifiers = []      # modificadores opcionales: ctrl, alt, shift, cmd
key = "alt_r"       # tecla principal (Option derecha por defecto)

[audio]
sample_rate = 16000
channels = 1
device = -1         # -1 = micrófono por defecto del sistema

[model]
engine = "whisper"
whisper_repo = "mlx-community/whisper-large-v3-turbo-q4"
language = ""       # "" = autodetección (español + inglés técnico)
                    # "es" = fuerza español

[feedback]
start_sound = true  # pitido suave al empezar a grabar
stop_sound = true   # pitido suave al soltar la tecla
format_lists = true # convierte "primero X, segundo Y" en lista con guiones
```

## Formato automático de texto

El texto transcrito pasa por un pipeline de post-procesado antes de pegarse:

- **Mayúsculas en siglas**: `json` → `JSON`, `api` → `API`, `sql` → `SQL`...
- **Nombres propios**: `javascript` → `JavaScript`, `github` → `GitHub`, `openai` → `OpenAI`...
- **Capitalización de frases**: primera letra de cada oración en mayúsculas
- **Preguntas en español**: añade `¿` de apertura cuando falta
- **Listas con ordinales**: si dices "primero huevos, segundo leche, tercero pan" lo convierte en:
  ```
  - Huevos
  - Leche
  - Pan
  ```

## Motor de transcripción

Usa [Whisper large-v3-turbo](https://huggingface.co/mlx-community/whisper-large-v3-turbo-q4) cuantizado a 4 bits para Apple Silicon vía [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper).

- Peso del modelo: ~450 MB
- Latencia típica: 1-3 segundos para frases cortas
- Funciona bien con mezcla de español e inglés técnico

## Gestión del servicio

WhisperFlow corre como un **LaunchAgent** de macOS: arranca automáticamente al iniciar sesión y se reinicia solo si peta. No necesitas abrirlo manualmente.

```bash
# Ver logs en tiempo real
tail -f ~/Library/Logs/whisperflow-local.log

# Parar el servicio
launchctl unload ~/Library/LaunchAgents/com.whisperflow.local.plist

# Arrancar o reiniciar el servicio
launchctl load ~/Library/LaunchAgents/com.whisperflow.local.plist

# Desinstalar completamente
bash uninstall.sh
```

## Estructura del proyecto

```
whisperflow-local/
├── src/
│   ├── main.py          # Orquestador principal y máquina de estados
│   ├── hotkey.py        # Listener global de teclado (pynput + CGEventTap)
│   ├── recorder.py      # Captura de audio (sounddevice)
│   ├── transcriber.py   # Motor de transcripción (mlx-whisper)
│   ├── paster.py        # Pegado via portapapeles + Cmd+V con restauración
│   └── formatter.py     # Post-procesado de texto
├── config.toml                      # Configuración
├── com.whisperflow.local.plist      # LaunchAgent (arranque automático)
├── install.sh                       # Script de instalación
├── uninstall.sh                     # Script de desinstalación
└── requirements.txt                 # Dependencias Python
```
