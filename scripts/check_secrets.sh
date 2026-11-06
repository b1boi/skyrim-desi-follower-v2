#!/usr/bin/env bash
# Pre-commit secret scanning script
set -euo pipefail

# 1. Check for staged .env files
staged_env=$(git diff --cached --name-only | grep -E '(^|/)\.env(\.|$)' || true)
if [ -n "$staged_env" ]; then
    echo "ERROR: Attempting to commit an .env file:"
    echo "$staged_env"
    echo "Aborting commit."
    exit 1
fi

# 2. Check staged diff for secret patterns and private key headers (excluding scripts/check_secrets.sh)
STAGED_DIFF=$(git diff --cached -U0 -- . ':(exclude)scripts/check_secrets.sh')

if [ -n "$STAGED_DIFF" ]; then
    # Check for private keys
    if echo "$STAGED_DIFF" | grep -E "^\+" | grep -E "BEGIN (RSA|OPENSSH|EC|DSA)? ?PRIVATE KEY" > /dev/null; then
        echo "ERROR: Possible private key detected in staged changes."
        exit 1
    fi

    # Patterns: OpenAI sk-, HuggingFace hf_, GitHub ghp_, Anthropic sk-ant-, generic api_key assignments
    SECRET_PATTERN='(sk-[a-zA-Z0-9]{20,}|sk-ant-[a-zA-Z0-9_\-]{20,}|gh[pousr]_[a-zA-Z0-9]{36,}|hf_[a-zA-Z0-9]{34,}|[a-zA-Z0-9_]*(?:api_key|apikey|secret_key|auth_token)\s*=\s*["'\''"][a-zA-Z0-9_\-]{16,}["'\''"])'

    SUSPECTS=$(echo "$STAGED_DIFF" | grep -E "^\+" | grep -v "^\+\+\+" | grep -E -i "$SECRET_PATTERN" || true)

    if [ -n "$SUSPECTS" ]; then
        echo "ERROR: Suspected API key or token found in staged changes:"
        echo "$SUSPECTS"
        echo "Please store secrets in .env (which is gitignored)."
        exit 1
    fi
fi

exit 0
