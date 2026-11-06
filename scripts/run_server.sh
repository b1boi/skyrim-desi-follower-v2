#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONPATH="${REPO_ROOT}/upstream/Mantella:${PYTHONPATH:-}"

echo "[INFO] Starting native Mantella server on Linux..."
exec "${REPO_ROOT}/.venv/bin/python" "${REPO_ROOT}/upstream/Mantella/main.py" "$@"
