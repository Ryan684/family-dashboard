#!/bin/bash
set -euo pipefail

# Only run in remote/web environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "=== Setting up Python 3.14 ==="
apt-get install -y python3.14 python3.14-venv

echo "=== Installing backend dependencies ==="
cd "$CLAUDE_PROJECT_DIR/backend"
python3.14 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -e ".[dev]" --quiet

# Add venv bin to PATH for the whole session so python, pytest, ruff all resolve correctly
echo "export PATH=\"$CLAUDE_PROJECT_DIR/backend/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"

echo "=== Installing frontend dependencies ==="
cd "$CLAUDE_PROJECT_DIR/frontend"
npm install --silent

echo "=== Environment ready ==="
