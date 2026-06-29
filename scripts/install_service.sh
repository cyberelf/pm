#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.cyberelf.weeklyreports"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
PORT="${PORT:-8765}"
FAKE_PROVIDER="${REPORTS_FAKE_PROVIDER:-0}"
SERVICE_PATH="${PATH:-/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin}"

mkdir -p "$HOME/Library/LaunchAgents" "$ROOT_DIR/data"

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
fi

python3 - "$PLIST" "$ROOT_DIR" "$PORT" "$FAKE_PROVIDER" "$SERVICE_PATH" <<'PY'
import plistlib
import sys
from pathlib import Path

plist_path = Path(sys.argv[1])
root = Path(sys.argv[2])
port = sys.argv[3]
fake_provider = sys.argv[4]
service_path = sys.argv[5]
data = {
    "Label": "com.cyberelf.weeklyreports",
    "ProgramArguments": ["/usr/bin/python3", "-u", str(root / "run.py")],
    "WorkingDirectory": str(root),
    "EnvironmentVariables": {
        "PORT": port,
        "REPORTS_FAKE_PROVIDER": fake_provider,
        "NO_PROXY": "127.0.0.1,localhost",
        "PATH": service_path,
    },
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

echo "Installed $LABEL"
echo "URL: http://127.0.0.1:$PORT"
echo "Logs: $ROOT_DIR/data/server.log and $ROOT_DIR/data/server.err.log"
