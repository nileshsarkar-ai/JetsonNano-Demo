#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$PROJECT_ROOT/scripts/check_board.py" --strict
# Uses Ubuntu/JetPack repositories. Does not replace Python or CUDA.
sudo apt-get update
sudo apt-get install -y build-essential gcc-8 g++-8 git ca-certificates \
  python3 ffmpeg
if [[ "${WITH_AUDIO:-0}" == "1" ]]; then
  sudo apt-get install -y alsa-utils espeak-ng
fi
