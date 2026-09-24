#!/usr/bin/env bash
# Prefer an installed Python 3.11; never replace JetPack's system Python.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SELECTED_PYTHON=""
if [[ -n "${DEMO_PYTHON:-}" ]]; then
  SELECTED_PYTHON="$(command -v "$DEMO_PYTHON")" || { echo 'DEMO_PYTHON not found.' >&2; exit 1; }
else
  for candidate in python3.11 python python3; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import sys; sys.exit(sys.version_info[:2] != (3, 11))' 2>/dev/null; then
      SELECTED_PYTHON="$(command -v "$candidate")"
      break
    fi
  done
  if [[ -z "$SELECTED_PYTHON" ]]; then
    SELECTED_PYTHON="$(command -v python3)" || { echo 'Python 3.6+ is required.' >&2; exit 1; }
  fi
fi
"$SELECTED_PYTHON" -c 'import sys, ssl, sqlite3, ctypes; sys.exit(sys.version_info < (3, 6))' || {
  echo 'Selected Python needs version 3.6+ and working ssl, sqlite3 and ctypes modules. Set DEMO_PYTHON=/usr/bin/python3 to use JetPack Python.' >&2
  exit 1
}
exec "$SELECTED_PYTHON" "$PROJECT_ROOT/scripts/demo_menu.py" "$@"
