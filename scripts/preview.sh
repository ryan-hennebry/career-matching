#!/bin/bash
# Preview an HTML file on localhost:8800
# Usage: scripts/preview.sh <filepath>
# Server persists after script exit. PID written to /tmp/jsa-preview.pid

set -e

if [ -z "$1" ]; then
  echo "Usage: scripts/preview.sh <filepath>"
  exit 1
fi

FILEPATH="$1"
if [ ! -f "$FILEPATH" ]; then
  echo "File not found: $FILEPATH"
  exit 1
fi

PARENT_DIR=$(dirname "$FILEPATH")
FILENAME=$(basename "$FILEPATH")
PORT=8800
PID_FILE="/tmp/jsa-preview.pid"

# Kill existing process on port
if [ -f "$PID_FILE" ]; then
  kill "$(cat "$PID_FILE")" 2>/dev/null || true
  rm -f "$PID_FILE"
fi
lsof -ti:$PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

# Start server in background with nohup — no trap cleanup
cd "$PARENT_DIR"
nohup python3 -m http.server $PORT --bind 127.0.0.1 &>/dev/null &
echo $! > "$PID_FILE"

# Health check
sleep 1
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/$FILENAME" | grep -q "200"; then
  echo "Preview: http://localhost:$PORT/$FILENAME"
  echo "Server PID: $(cat "$PID_FILE")"
  open "http://localhost:$PORT/$FILENAME"
else
  echo "Server failed to start"
  kill "$(cat "$PID_FILE")" 2>/dev/null || true
  rm -f "$PID_FILE"
  exit 1
fi
