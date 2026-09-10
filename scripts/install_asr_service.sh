#!/usr/bin/env bash
# Install the whisper.cpp ASR server as a per-user background service that
# starts at login. One script, three platforms:
#   macOS    LaunchAgent (launchd)          — whisper-cpp via Homebrew
#   Linux    systemd user service           — whisper.cpp built or on PATH
#   Windows  .bat in the Startup folder     — run from Git Bash; or use the
#            Linux flow inside WSL2 instead
#
# knobs (env or repo-root .env): ASR_PORT (default 8766), ASR_MODEL,
# WHISPER_SERVER (path to the whisper-server binary).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.cyberelf.whisperasr"
UNIT_NAME="whisper-asr"
ASR_PORT="${ASR_PORT:-8766}"
MODEL="${ASR_MODEL:-$ROOT_DIR/data/models/ggml-large-v3-turbo-q5_0.bin}"
LOG_DIR="$ROOT_DIR/data"
LOG_FILE="$LOG_DIR/whisper.log"
OS="$(uname -s)"
STARTUP_DIR="${APPDATA:-$HOME/AppData/Roaming}/Microsoft/Windows/Start Menu/Programs/Startup"

if [ ! -f "$MODEL" ]; then
  echo "whisper model not found at $MODEL" >&2
  echo "download one, e.g.:" >&2
  echo "  mkdir -p '$ROOT_DIR/data/models'" >&2
  echo "  curl -L -o '$MODEL' https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin" >&2
  echo "  (original: https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin)" >&2
  exit 1
fi

find_server() {
  if [ -n "${WHISPER_SERVER:-}" ]; then
    printf '%s' "$WHISPER_SERVER"
    return
  fi
  case "$OS" in
    Darwin)
      if [ -x /opt/homebrew/bin/whisper-server ]; then
        printf '%s' /opt/homebrew/bin/whisper-server
      elif [ -x /usr/local/bin/whisper-server ]; then
        printf '%s' /usr/local/bin/whisper-server
      fi
      ;;
    Linux)
      command -v whisper-server || true
      ;;
    MINGW*|MSYS*|CYGWIN*)
      command -v whisper-server.exe || true
      ;;
  esac
}

SERVER="$(find_server)"
if [ -z "$SERVER" ] || [ ! -e "$SERVER" ]; then
  echo "whisper-server binary not found (set WHISPER_SERVER to its path)" >&2
  case "$OS" in
    Darwin) echo "install it with: brew install whisper-cpp" >&2 ;;
    MINGW*|MSYS*|CYGWIN*) echo "download a Windows build from https://github.com/ggml-org/whisper.cpp/releases or build one with cmake" >&2 ;;
    *) echo "build it with: git clone https://github.com/ggml-org/whisper.cpp && cmake -S whisper.cpp -B whisper.cpp/build && cmake --build whisper.cpp/build --target whisper-server" >&2 ;;
  esac
  exit 1
fi

mkdir -p "$LOG_DIR"

install_report() {
  echo "Installed $1 (whisper-server on http://127.0.0.1:$ASR_PORT)"
  echo "Model: $MODEL"
  echo "Log: $LOG_FILE"
}

case "$OS" in
Darwin)
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
  mkdir -p "$HOME/Library/LaunchAgents"

  if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
    launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
  fi

  python3 - "$PLIST" "$SERVER" "$MODEL" "$ASR_PORT" "$LOG_FILE" <<'PY'
import plistlib
import sys
from pathlib import Path

plist_path = Path(sys.argv[1])
server = sys.argv[2]
model = sys.argv[3]
port = sys.argv[4]
log_file = sys.argv[5]
data = {
    "Label": "com.cyberelf.whisperasr",
    "ProgramArguments": [
        server,
        "--host", "127.0.0.1",
        "--port", port,
        "--model", model,
        "--language", "auto",
    ],
    "RunAtLoad": True,
    "KeepAlive": True,
    "StandardOutPath": log_file,
    "StandardErrorPath": log_file,
}
with plist_path.open("wb") as fh:
    plistlib.dump(data, fh)
PY

  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  launchctl kickstart -k "gui/$(id -u)/$LABEL"
  install_report "$LABEL"
  ;;

Linux)
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl not found: this flow needs systemd. Run the server manually instead:" >&2
    echo "  $SERVER --host 127.0.0.1 --port $ASR_PORT --model '$MODEL' --language auto >> '$LOG_FILE' 2>&1 &" >&2
    exit 1
  fi
  UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
  UNIT="$UNIT_DIR/$UNIT_NAME.service"
  mkdir -p "$UNIT_DIR"

  cat > "$UNIT" <<EOF
[Unit]
Description=whisper.cpp ASR server for zreport

[Service]
ExecStart="$SERVER" --host 127.0.0.1 --port $ASR_PORT --model "$MODEL" --language auto
Restart=always
StandardOutput=append:$LOG_FILE
StandardError=append:$LOG_FILE

[Install]
WantedBy=default.target
EOF

  systemctl --user daemon-reload
  systemctl --user enable --now "$UNIT_NAME.service" >/dev/null 2>&1 || true
  systemctl --user restart "$UNIT_NAME.service"
  if ! loginctl show-user "$(id -un)" --property=Linger 2>/dev/null | grep -q '=yes'; then
    echo "note: run 'sudo loginctl enable-linger $(id -un)' once so the service survives logout"
  fi
  install_report "$UNIT_NAME.service"
  ;;

MINGW*|MSYS*|CYGWIN*)
  # A .bat in the user's Startup folder autostarts the server at login.
  # It runs in a (minimize it yourself) console window; WSL2 users who want
  # a hidden service should use the Linux flow inside WSL instead.
  mkdir -p "$STARTUP_DIR"
  BAT="$STARTUP_DIR/whisper-asr.bat"
  {
    echo '@echo off'
    echo "rem Generated by scripts/install_asr_service.sh ($(date '+%F %T'))"
    echo "\"$(cygpath -w "$SERVER")\" --host 127.0.0.1 --port $ASR_PORT --model \"$(cygpath -w "$MODEL")\" --language auto >> \"$(cygpath -w "$LOG_FILE")\" 2>&1"
  } > "$BAT"

  BAT_WIN="$(cygpath -w "$BAT")"
  MSYS2_ARG_CONV_EXCL='*' cmd /c start "whisper-asr" "$BAT_WIN" >/dev/null
  install_report "$BAT"
  echo "Autostart: $BAT_WIN"
  ;;

*)
  echo "unsupported platform: $OS (macOS, Linux, or Windows via Git Bash/WSL2)" >&2
  exit 1
  ;;
esac
