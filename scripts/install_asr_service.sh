#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.cyberelf.whisperasr"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
ASR_PORT="${ASR_PORT:-8766}"
MODEL="${ASR_MODEL:-$ROOT_DIR/data/models/ggml-large-v3-turbo-q5_0.bin}"
WHISPER_SERVER="${WHISPER_SERVER:-/opt/homebrew/bin/whisper-server}"
LOG_DIR="$ROOT_DIR/data"

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR" "$(dirname "$MODEL")"

if [ ! -x "$WHISPER_SERVER" ]; then
  echo "whisper-server not found at $WHISPER_SERVER; install it with: brew install whisper-cpp" >&2
  exit 1
fi
if [ ! -f "$MODEL" ]; then
  echo "whisper model not found at $MODEL" >&2
  echo "download one, e.g.: curl -L -o '$MODEL' https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin" >&2
  exit 1
fi

if launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
  launchctl bootout "gui/$(id -u)" "$PLIST" >/dev/null 2>&1 || true
fi

python3 - "$PLIST" "$WHISPER_SERVER" "$MODEL" "$ASR_PORT" "$LOG_DIR" <<'PY'
import plistlib
import sys
from pathlib import Path

plist_path = Path(sys.argv[1])
server = sys.argv[2]
model = sys.argv[3]
port = sys.argv[4]
log_dir = Path(sys.argv[5])
data = {
    "Label": "com.cyberelf.whisperasr",
    "ProgramArguments": [
        server,
        "--host", "127.0.0.1",
        "--port", port,
        "--model", model,
    ],
    "RunAtLoad": True,
    "KeepAlive": True,
    "StandardOutPath": str(log_dir / "whisper.log"),
    "StandardErrorPath": str(log_dir / "whisper.log"),
}
with plist_path.open("wb") as fh:
    plistlib.dump(data, fh)
PY

launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "Installed $LABEL (whisper-server on http://127.0.0.1:$ASR_PORT)"
echo "Model: $MODEL"
echo "Log: $LOG_DIR/whisper.log"
