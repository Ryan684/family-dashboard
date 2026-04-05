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

echo "=== Installing Claude Code skills ==="
# Clone the Anthropic skills marketplace (public repo) and install frontend-design.
# github.com is whitelisted in the sandbox proxy, but git needs http.proxy set explicitly —
# the sandbox only sets GLOBAL_AGENT_HTTP_PROXY which git does not read automatically.
if git \
    -c "http.proxy=${GLOBAL_AGENT_HTTP_PROXY:-}" \
    -c credential.helper= \
    clone --depth 1 \
    https://github.com/anthropics/anthropic-agent-skills.git \
    /tmp/anthropic-agent-skills 2>/dev/null; then
  claude plugins marketplace add /tmp/anthropic-agent-skills --scope user 2>/dev/null || true
  claude plugins install frontend-design --scope user 2>/dev/null || true
  rm -rf /tmp/anthropic-agent-skills
  echo "frontend-design skill installed"
else
  echo "Warning: Could not reach skills marketplace — frontend-design skill unavailable this session"
fi

echo "=== Environment ready ==="
