#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$PROJECT_ROOT/scripts/check_board.py" --strict
sudo apt-get update
sudo apt-get install -y v4l-utils gstreamer1.0-tools gstreamer1.0-plugins-good
