#!/usr/bin/env bash
# Original Nano / JetPack 4. No pip or replacement Python required.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v python3 >/dev/null || { echo 'Python 3 is required.' >&2; exit 1; }
exec python3 "$PROJECT_ROOT/scripts/demo_menu.py" "$@"
