#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT_DIR/data/server.pid"
LOG_FILE="$ROOT_DIR/data/server.log"
PORT="${PORT:-8765}"

mkdir -p "$ROOT_DIR/data"

if [[ -f "$PID_FILE" ]]; then
  PID="$(cat "$PID_FILE")"
  if kill -0 "$PID" 2>/dev/null; then
    echo "Server already running at http://127.0.0.1:$PORT (pid $PID)"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

cd "$ROOT_DIR"
nohup env \
  REPORTS_FAKE_PROVIDER="${REPORTS_FAKE_PROVIDER:-0}" \
  PORT="$PORT" \
  NO_PROXY="127.0.0.1,localhost,${NO_PROXY:-}" \
  python3 -u run.py </dev/null >>"$LOG_FILE" 2>&1 &
echo "$!" > "$PID_FILE"

sleep 0.5
if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Server failed to start. See $LOG_FILE" >&2
  exit 1
fi

echo "Server running at http://127.0.0.1:$PORT"
echo "PID: $(cat "$PID_FILE")"
echo "Log: $LOG_FILE"
