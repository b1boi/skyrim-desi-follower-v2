#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONPATH="${REPO_ROOT}/upstream/Mantella:${PYTHONPATH:-}"
export MANTELLA_USER_FOLDER="${MANTELLA_USER_FOLDER:-${REPO_ROOT}/run/mantella_user}"
export MANTELLA_VOICE_DIR="${MANTELLA_VOICE_DIR:-${REPO_ROOT}/run/mantella_user/voicelines}"

mkdir -p "${MANTELLA_USER_FOLDER}" "${MANTELLA_VOICE_DIR}"

if [ -f "${REPO_ROOT}/.venv/bin/python" ]; then
    PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
elif [ -n "${VIRTUAL_ENV:-}" ] && [ -f "${VIRTUAL_ENV}/bin/python" ]; then
    PYTHON_BIN="${VIRTUAL_ENV}/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "ERROR: Could not find Python binary." >&2
    exit 1
fi

echo "[INFO] Starting native Mantella server on Linux using ${PYTHON_BIN}..."
exec "${PYTHON_BIN}" "${REPO_ROOT}/upstream/Mantella/main.py" "$@"

