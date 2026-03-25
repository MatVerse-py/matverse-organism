#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi

python3 -c "import requests" 2>/dev/null || {
  echo "Installing requests..."
  python3 -m pip install --user requests
}

exec python3 organism_guardian.py "$@"
