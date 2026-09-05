#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.cyberelf.weeklyreports"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

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
SERVICE_PATH="${PATH:-/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin}"

# Self-signed cert so phones can use microphone access over HTTPS (port 8443).
TLS_CERT="$ROOT_DIR/data/tls/service.crt"
TLS_KEY="$ROOT_DIR/data/tls/service.key"
if [ -n "$TLS_PORT" ] && command -v openssl >/dev/null 2>&1 && [ ! -f "$TLS_CERT" ]; then
  mkdir -p "$ROOT_DIR/data/tls"
  TLS_SAN="DNS:localhost,IP:127.0.0.1"
  [ -n "$HOST" ] && TLS_SAN="$TLS_SAN,IP:$HOST"
  if ! openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
    -keyout "$TLS_KEY" -out "$TLS_CERT" \
    -subj "/CN=weeklyreports" -addext "subjectAltName=$TLS_SAN" >/dev/null 2>&1; then
    openssl req -x509 -newkey rsa:2048 -sha256 -days 3650 -nodes \
      -keyout "$TLS_KEY" -out "$TLS_CERT" -subj "/CN=weeklyreports" >/dev/null 2>&1
  fi
fi
if [ -n "$TLS_PORT" ] && [ ! -f "$TLS_CERT" ]; then
  echo "TLS disabled: openssl unavailable or certificate generation failed" >&2
  TLS_PORT=""
fi

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT_DIR/data"

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
fi

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
    "Label": "com.cyberelf.weeklyreports",
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

HOST_DISPLAY="${REPORTS_HOST:-127.0.0.1}"
echo "Installed $LABEL"
echo "URL: http://$HOST_DISPLAY:$PORT"
if [ -n "$TLS_PORT" ]; then
  echo "HTTPS (phones, microphone): https://$HOST_DISPLAY:$TLS_PORT (accept the self-signed certificate warning)"
fi
echo "Logs: $ROOT_DIR/data/server.log and $ROOT_DIR/data/server.err.log"
