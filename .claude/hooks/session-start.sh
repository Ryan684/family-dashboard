#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Skills installation — runs in ALL environments (web and local CLI).
# Skills are plain markdown directories — no plugin CLI needed.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Python 3.14 + backend venv — web/remote only (already present locally)
# ---------------------------------------------------------------------------
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Python 3.14 + backend venv
# ---------------------------------------------------------------------------
echo "=== Setting up Python 3.14 ==="
apt-get install -y python3.14 python3.14-venv

echo "=== Installing backend dependencies ==="
cd "$CLAUDE_PROJECT_DIR/backend"
python3.14 -m venv .venv
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -e ".[dev]" --quiet

# Persist the venv bin on PATH for the rest of the session.
# CLAUDE_ENV_FILE is set by the Claude Code harness in web sessions; guard
# against it being absent so this line never kills the script.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$CLAUDE_PROJECT_DIR/backend/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
else
  echo "Warning: CLAUDE_ENV_FILE not set — PATH not persisted; activate venv manually if needed"
  export PATH="$CLAUDE_PROJECT_DIR/backend/.venv/bin:$PATH"
fi

# ---------------------------------------------------------------------------
# Frontend node_modules
# ---------------------------------------------------------------------------
echo "=== Installing frontend dependencies ==="
cd "$CLAUDE_PROJECT_DIR/frontend"
npm install --silent

echo "=== Environment ready ==="
