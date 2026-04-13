#!/bin/bash
set -e

PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/com.whisperflow.local.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.whisperflow.local.plist"

echo "Instalando WhisperFlow Local como LaunchAgent..."
cp "$PLIST_SRC" "$PLIST_DST"
launchctl load "$PLIST_DST"
echo "✓ Instalado. Arrancará automáticamente al iniciar sesión."
echo ""
echo "IMPORTANTE: concede permisos de Accesibilidad e Input Monitoring"
echo "al binario de Python del proyecto:"
echo "  $(dirname "$PLIST_SRC")/.venv/bin/python"
echo ""
echo "Ajustes del sistema → Privacidad y seguridad → Accesibilidad"
echo "Ajustes del sistema → Privacidad y seguridad → Monitorización de dispositivos de entrada"
echo ""
echo "Logs: tail -f ~/Library/Logs/whisperflow-local.log"
