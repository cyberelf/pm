#!/usr/bin/env bash
set -euo pipefail

LABEL="com.cyberelf.weeklyreports"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [[ -f "$PLIST" ]]; then
  launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
  rm -f "$PLIST"
fi

echo "Uninstalled $LABEL"
