#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python"
PLIST_SRC="$SCRIPT_DIR/com.whisperflow.local.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.whisperflow.local.plist"

# Matar proceso anterior si sigue corriendo
pkill -f "$SCRIPT_DIR/src/main.py" 2>/dev/null || true
sleep 0.5

cp "$PLIST_SRC" "$PLIST_DST"

# Cargar (o recargar) el LaunchAgent
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"

echo ""
echo "✓ WhisperFlow instalado. Arranca automáticamente al iniciar sesión."
echo ""
echo "Permisos necesarios para el binario: $PYTHON"
echo "  → Ajustes → Privacidad → Accesibilidad"
echo "  → Ajustes → Privacidad → Monitorización de dispositivos de entrada"
echo ""
echo "Logs: tail -f ~/Library/Logs/whisperflow-local.log"
