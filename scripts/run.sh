#!/usr/bin/env zsh
# Boot the CodeCraftHub Flask server.
#
#   ./scripts/run.sh          # http://localhost:5000/api/courses
#   PORT=8000 ./scripts/run.sh
#
# Creates a local .venv on first run and installs requirements.

set -euo pipefail

SCRIPT_DIR="${0:A:h}"
ROOT_DIR="${SCRIPT_DIR:h}"
cd "$ROOT_DIR"

PORT="${PORT:-5000}"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "▶ Creating virtualenv at ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet -r requirements.txt
fi

echo "▶ Starting CodeCraftHub on http://localhost:${PORT}/api/courses"
echo "  (Ctrl-C to stop)"
PORT="$PORT" exec "$VENV_DIR/bin/python" run.py

