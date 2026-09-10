#!/usr/bin/env bash
# Install the zreport server as a per-user background service that
# starts at login. One script, three platforms:
#   macOS    LaunchAgent (launchd)
#   Linux    systemd user service (zreport.service)
#   Windows  .bat in the Startup folder — run from Git Bash; or use the
#            Linux flow inside WSL2 instead
#
# knobs (env or repo-root .env): PORT, REPORTS_HOST, REPORTS_TLS_PORT,
# REPORTS_FAKE_PROVIDER.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.cyberelf.zreport"
UNIT_NAME="zreport"
OS="$(uname -s)"
STARTUP_DIR="${APPDATA:-$HOME/AppData/Roaming}/Microsoft/Windows/Start Menu/Programs/Startup"

# .env supplies defaults for missing variables; real environment always wins.
if [ -f "$ROOT_DIR/.env" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|\#*) continue ;; esac
    case "$line" in *=*) ;; *) continue ;; esac
    key="${line%%=*}"
    value="${line#*=}"
    if [ -n "$key" ] && [ -z "${!key:-}" ]; then
      export "$key=$value"
    fi
  done < "$ROOT_DIR/.env"
fi

PORT="${PORT:-8765}"
FAKE_PROVIDER="${REPORTS_FAKE_PROVIDER:-0}"
HOST="${REPORTS_HOST:-}"
TLS_PORT="${REPORTS_TLS_PORT:-8443}"

# Self-signed cert so phones can use microphone access over HTTPS (port 8443).
TLS_CERT="$ROOT_DIR/data/tls/service.crt"
TLS_KEY="$ROOT_DIR/data/tls/service.key"
if [ -n "$TLS_PORT" ] && command -v openssl >/dev/null 2>&1 && [ ! -f "$TLS_CERT" ]; then
  mkdir -p "$ROOT_DIR/data/tls"
  TLS_SAN="DNS:localhost,IP:127.0.0.1"
  [ -n "$HOST" ] && TLS_SAN="$TLS_SAN,IP:$HOST"
  if ! openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
    -keyout "$TLS_KEY" -out "$TLS_CERT" \
    -subj "/CN=zreport" -addext "subjectAltName=$TLS_SAN" >/dev/null 2>&1; then
    openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
      -keyout "$TLS_KEY" -out "$TLS_CERT" -subj "/CN=zreport" >/dev/null 2>&1
  fi
fi
if [ -n "$TLS_PORT" ] && [ ! -f "$TLS_CERT" ]; then
  echo "TLS disabled: openssl unavailable or certificate generation failed" >&2
  TLS_PORT=""
fi

mkdir -p "$ROOT_DIR/data"
HOST_DISPLAY="${HOST:-127.0.0.1}"

report() {
  echo "Installed $1"
  echo "URL: http://$HOST_DISPLAY:$PORT"
  if [ -n "$TLS_PORT" ]; then
    echo "HTTPS (phones, microphone): https://$HOST_DISPLAY:$TLS_PORT (accept the self-signed certificate warning)"
  fi
  echo "Logs: $ROOT_DIR/data/server.log and $ROOT_DIR/data/server.err.log"
}

case "$OS" in
Darwin)
  PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
  mkdir -p "$HOME/Library/LaunchAgents"

  if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
    launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
  fi

  SERVICE_PATH="${PATH:-/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin}"
  python3 - "$PLIST" "$ROOT_DIR" "$PORT" "$FAKE_PROVIDER" "$SERVICE_PATH" "$HOST" "$TLS_PORT" <<'PY'
import plistlib
import sys
from pathlib import Path

plist_path = Path(sys.argv[1])
root = Path(sys.argv[2])
port = sys.argv[3]
fake_provider = sys.argv[4]
service_path = sys.argv[5]
host = sys.argv[6]
tls_port = sys.argv[7]
environment = {
    "PORT": port,
    "REPORTS_FAKE_PROVIDER": fake_provider,
    "NO_PROXY": "127.0.0.1,localhost",
    "PATH": service_path,
}
if host:
    environment["REPORTS_HOST"] = host
if tls_port:
    environment["REPORTS_TLS_PORT"] = tls_port
data = {
    "Label": "com.cyberelf.zreport",
    "ProgramArguments": ["/usr/bin/python3", "-u", str(root / "run.py")],
    "WorkingDirectory": str(root),
    "EnvironmentVariables": environment,
    "RunAtLoad": True,
    "KeepAlive": True,
    "StandardOutPath": str(root / "data" / "server.log"),
    "StandardErrorPath": str(root / "data" / "server.err.log"),
}
with plist_path.open("wb") as fh:
    plistlib.dump(data, fh)
PY

  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  launchctl kickstart -k "gui/$(id -u)/$LABEL"
  report "$LABEL"
  ;;

Linux)
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl not found: this flow needs systemd. Start the server manually with scripts/start_server.sh" >&2
    exit 1
  fi
  PY3="$(command -v python3)"
  if [ -z "$PY3" ]; then
    echo "python3 not found on PATH; install Python 3 first" >&2
    exit 1
  fi
  UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
  UNIT="$UNIT_DIR/$UNIT_NAME.service"
  mkdir -p "$UNIT_DIR"

  {
    echo "[Unit]"
    echo "Description=zreport server"
    echo ""
    echo "[Service]"
    echo "WorkingDirectory=$ROOT_DIR"
    echo "ExecStart=\"$PY3\" -u run.py"
    echo "Environment=PORT=$PORT"
    echo "Environment=REPORTS_FAKE_PROVIDER=$FAKE_PROVIDER"
    echo "Environment=NO_PROXY=127.0.0.1,localhost"
    [ -n "$HOST" ] && echo "Environment=REPORTS_HOST=$HOST"
    [ -n "$TLS_PORT" ] && echo "Environment=REPORTS_TLS_PORT=$TLS_PORT"
    echo "Restart=always"
    echo "StandardOutput=append:$ROOT_DIR/data/server.log"
    echo "StandardError=append:$ROOT_DIR/data/server.err.log"
    echo ""
    echo "[Install]"
    echo "WantedBy=default.target"
  } > "$UNIT"

  systemctl --user daemon-reload
  systemctl --user enable --now "$UNIT_NAME.service" >/dev/null 2>&1 || true
  systemctl --user restart "$UNIT_NAME.service"
  if ! loginctl show-user "$(id -un)" --property=Linger 2>/dev/null | grep -q '=yes'; then
    echo "note: run 'sudo loginctl enable-linger $(id -un)' once so the service survives logout"
  fi
  report "$UNIT_NAME.service"
  ;;

MINGW*|MSYS*|CYGWIN*)
  # A .bat in the user's Startup folder autostarts the server at login.
  # It runs in a (minimize it yourself) console window; WSL2 users who want
  # a hidden service should use the Linux flow inside WSL instead.
  mkdir -p "$STARTUP_DIR"
  BAT="$STARTUP_DIR/zreport.bat"
  {
    echo '@echo off'
    echo "rem Generated by scripts/install_service.sh ($(date '+%F %T'))"
    echo "cd /d \"$(cygpath -w "$ROOT_DIR")\""
    echo "set PORT=$PORT"
    echo "set REPORTS_FAKE_PROVIDER=$FAKE_PROVIDER"
    echo "set NO_PROXY=127.0.0.1,localhost"
    [ -n "$HOST" ] && echo "set REPORTS_HOST=$HOST"
    [ -n "$TLS_PORT" ] && echo "set REPORTS_TLS_PORT=$TLS_PORT"
    echo "python -u run.py >> \"$(cygpath -w "$ROOT_DIR/data/server.log")\" 2>> \"$(cygpath -w "$ROOT_DIR/data/server.err.log")\""
  } > "$BAT"

  BAT_WIN="$(cygpath -w "$BAT")"
  MSYS2_ARG_CONV_EXCL='*' cmd /c start "zreport" "$BAT_WIN" >/dev/null
  report "$BAT"
  echo "Autostart: $BAT_WIN"
  ;;

*)
  echo "unsupported platform: $OS (macOS, Linux, or Windows via Git Bash/WSL2)" >&2
  exit 1
  ;;
esac
