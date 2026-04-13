#!/bin/bash
PLIST_DST="$HOME/Library/LaunchAgents/com.whisperflow.local.plist"

if [ -f "$PLIST_DST" ]; then
    launchctl unload "$PLIST_DST"
    rm "$PLIST_DST"
    echo "✓ WhisperFlow Local desinstalado."
else
    echo "No estaba instalado."
fi
