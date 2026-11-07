#!/usr/bin/env bash
# scripts/install_hooks.sh - Installs git pre-commit hooks for secret detection
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Ensure scripts are executable
chmod +x "${REPO_ROOT}/scripts/check_secrets.sh"
if [ -f "${REPO_ROOT}/.githooks/pre-commit" ]; then
    chmod +x "${REPO_ROOT}/.githooks/pre-commit"
fi

# 1. Point Git core.hooksPath to the tracked .githooks directory
git -C "${REPO_ROOT}" config core.hooksPath .githooks

# 2. Also symlink into .git/hooks for tooling that doesn't respect core.hooksPath
GIT_DIR=$(git -C "${REPO_ROOT}" rev-parse --git-dir)
if [ -d "${GIT_DIR}/hooks" ] && [ -w "${GIT_DIR}/hooks" ]; then
    ln -sf "../../scripts/check_secrets.sh" "${GIT_DIR}/hooks/pre-commit" 2>/dev/null || true
    chmod +x "${GIT_DIR}/hooks/pre-commit" 2>/dev/null || true
fi

echo "[SUCCESS] Pre-commit hooks installed successfully:"
echo "  - Git core.hooksPath configured to '.githooks'"
echo "  - Pre-commit secret scanning active via scripts/check_secrets.sh"
