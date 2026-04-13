#!/bin/bash
APP_BUNDLE="/Applications/WhisperFlowLocal.app"
PLIST="$HOME/Library/LaunchAgents/com.whisperflow.local.plist"

if [ -d "$APP_BUNDLE" ]; then
    rm -rf "$APP_BUNDLE"
    echo "✓ $APP_BUNDLE eliminado."
else
    echo "La app no estaba instalada."
fi

if [ -f "$PLIST" ]; then
    launchctl unload "$PLIST" 2>/dev/null || true
    rm "$PLIST"
    echo "✓ LaunchAgent eliminado."
fi

echo ""
echo "Si añadiste la app a Elementos de inicio de sesión, elimínala manualmente:"
echo "Ajustes del sistema → General → Elementos de inicio de sesión"
