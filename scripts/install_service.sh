#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.cyberelf.weeklyreports"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PORT="${PORT:-8765}"
FAKE_PROVIDER="${REPORTS_FAKE_PROVIDER:-0}"
HOST="${REPORTS_HOST:-}"
SERVICE_PATH="${PATH:-/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin}"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT_DIR/data"

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
fi

python3 - "$PLIST" "$ROOT_DIR" "$PORT" "$FAKE_PROVIDER" "$SERVICE_PATH" "$HOST" <<'PY'
import plistlib
import sys
from pathlib import Path

plist_path = Path(sys.argv[1])
root = Path(sys.argv[2])
port = sys.argv[3]
fake_provider = sys.argv[4]
service_path = sys.argv[5]
host = sys.argv[6]
environment = {
    "PORT": port,
    "REPORTS_FAKE_PROVIDER": fake_provider,
    "NO_PROXY": "127.0.0.1,localhost",
    "PATH": service_path,
}
if host:
    environment["REPORTS_HOST"] = host
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
echo "Logs: $ROOT_DIR/data/server.log and $ROOT_DIR/data/server.err.log"
