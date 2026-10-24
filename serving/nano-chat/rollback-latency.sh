#!/usr/bin/env bash
set -euo pipefail
jl exec 545719 -- sh -lc 'cp /home/nano-demo/rollback-before-latency/index.html /home/nano-demo/nano-chat/index.html; cp /home/nano-demo/rollback-before-latency/app.py /home/nano-demo/nano-chat/app.py; pkill -f "^/home/nano-demo/venv/bin/python /home/nano-demo/nano-chat/app.py$" || true; nohup /home/nano-demo/venv/bin/python /home/nano-demo/nano-chat/app.py >> /home/nano-demo/server.log 2>&1 < /dev/null &'
printf '%s\n' 'Restored. Refresh source portal, select Vision, then Start broadcast. Refresh remote viewers.'
