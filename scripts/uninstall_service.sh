#!/usr/bin/env bash
# Remove the per-user background service installed by install_service.sh /
# install_asr_service.sh. Works on macOS (LaunchAgent), Linux (systemd user
# unit), and Windows (Startup-folder .bat written from Git Bash).
#
# usage: scripts/uninstall_service.sh [reports|asr]   (default: reports)
set -euo pipefail

TARGET="${1:-reports}"
OS="$(uname -s)"
STARTUP_DIR="${APPDATA:-$HOME/AppData/Roaming}/Microsoft/Windows/Start Menu/Programs/Startup"

case "$TARGET" in
  reports) LABEL="com.cyberelf.zreport"; UNIT_NAME="zreport" ;;
  asr)     LABEL="com.cyberelf.whisperasr";    UNIT_NAME="whisper-asr" ;;
  *) echo "unknown target: $TARGET (use 'reports' or 'asr')" >&2; exit 1 ;;
esac

case "$OS" in
Darwin)
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
  if [[ -f "$PLIST" ]]; then
    launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
    rm -f "$PLIST"
  fi
  echo "Uninstalled $LABEL"
  ;;

Linux)
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user disable --now "$UNIT_NAME.service" >/dev/null 2>&1 || true
    UNIT="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/$UNIT_NAME.service"
    if [[ -f "$UNIT" ]]; then
      rm -f "$UNIT"
      systemctl --user daemon-reload
    fi
  fi
  echo "Uninstalled $UNIT_NAME.service"
  ;;

MINGW*|MSYS*|CYGWIN*)
  BAT="$STARTUP_DIR/$UNIT_NAME.bat"
  if [[ -f "$BAT" ]]; then
    rm -f "$BAT"
  fi
  echo "Uninstalled $BAT"
  ;;

*)
  echo "unsupported platform: $OS (macOS, Linux, or Windows via Git Bash/WSL2)" >&2
  exit 1
  ;;
esac
