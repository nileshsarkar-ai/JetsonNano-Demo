#!/usr/bin/env bash
# One-command core setup and chat for original Nano / JetPack 4 / Python 3.6.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
python3 scripts/check_board.py --strict
# Refuse to use an unrelated server already occupying the configured port.
python3 - <<'PY'
import json
import socket
from urllib.parse import urlparse
with open('config.json') as stream:
    endpoint = urlparse(json.load(stream)['server_url'])
if endpoint.scheme != 'http' or endpoint.hostname != '127.0.0.1':
    raise SystemExit('Expected an http://127.0.0.1 server URL')
with socket.socket() as sock:
    sock.settimeout(1)
    if sock.connect_ex((endpoint.hostname, endpoint.port or 80)) == 0:
        raise SystemExit('Server port is already in use. Stop the existing server first.')
PY
bash scripts/install_system.sh
JOBS="${JOBS:-2}" bash scripts/build_runtimes.sh
python3 scripts/download.py smol135-q4 whisper-tiny-en stories15m
mkdir -p runs
SERVER_LOG="$(mktemp "$PROJECT_ROOT/runs/server-XXXXXX.log")"
python3 scripts/serve.py >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!
cleanup() {
  local result=$?
  trap - EXIT
  kill "$SERVER_PID" 2>/dev/null || true
  wait "$SERVER_PID" 2>/dev/null || true
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "Starting model server. Log: $SERVER_LOG"
if ! python3 - "$SERVER_PID" <<'PY'
import json
import os
import sys
import time
import urllib.error
import urllib.request
with open('config.json') as stream:
    url = json.load(stream)['server_url'].rstrip('/') + '/health'
deadline = time.monotonic() + 600
while time.monotonic() < deadline:
    try:
        os.kill(int(sys.argv[1]), 0)
    except ProcessLookupError:
        raise SystemExit('Model server exited before becoming ready')
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                print('Model server is ready.')
                break
    except (urllib.error.URLError, OSError):
        pass
    time.sleep(1)
else:
    raise SystemExit('Model server did not become ready within 10 minutes')
PY
then
  tail -n 40 "$SERVER_LOG"
  exit 1
fi
python3 labs/chat.py
