#!/bin/bash
set -euo pipefail

# Only run in remote/web environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# ---------------------------------------------------------------------------
# Skills installation — runs FIRST and independently so it never gets skipped
# by failures in the Python/Node setup below.
# ---------------------------------------------------------------------------
echo "=== Installing Claude Code skills ==="
# Clone anthropics/skills and copy frontend-design into ~/.claude/skills/.
# Skills are plain markdown directories — no plugin CLI needed.
# github.com is whitelisted in the sandbox proxy, but git needs http.proxy set
# explicitly — the sandbox only sets GLOBAL_AGENT_HTTP_PROXY which git does not
# read automatically.
if git \
    -c "http.proxy=${GLOBAL_AGENT_HTTP_PROXY:-}" \
    -c credential.helper= \
    clone --depth 1 \
    https://github.com/anthropics/skills.git \
    /tmp/anthropic-skills 2>/dev/null; then
  mkdir -p ~/.claude/skills
  cp -r /tmp/anthropic-skills/skills/frontend-design ~/.claude/skills/frontend-design
  rm -rf /tmp/anthropic-skills
  echo "frontend-design skill installed"
else
  echo "Warning: Could not reach skills marketplace — frontend-design skill unavailable this session"
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
