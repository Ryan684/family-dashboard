#!/bin/bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Skills installation — runs in ALL environments (web and local CLI).
# Skills are plain markdown directories — no plugin CLI needed.
# ---------------------------------------------------------------------------
echo "=== Installing Claude Code skills ==="
# The frontend-design skill is enabled via enabledPlugins in .claude/settings.json,
# which references the pre-installed claude-plugins-official marketplace.
# This block is a fallback for web sessions where the marketplace may not be
# pre-populated. It installs the skill into the correct plugin structure so it
# is available from the next session onwards.
# Note: skills enabled via settings.json are loaded at session init (before hooks),
# so this fallback has no effect on the current session — only future ones.
PLUGIN_DIR="$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/frontend-design"
if [ ! -f "$PLUGIN_DIR/skills/frontend-design/SKILL.md" ]; then
  if git \
      -c "http.proxy=${GLOBAL_AGENT_HTTP_PROXY:-}" \
      -c credential.helper= \
      clone --depth 1 \
      https://github.com/anthropics/skills.git \
      /tmp/anthropic-skills 2>/dev/null; then
    mkdir -p "$PLUGIN_DIR/skills/frontend-design"
    mkdir -p "$PLUGIN_DIR/.claude-plugin"
    cp -r /tmp/anthropic-skills/skills/frontend-design/. "$PLUGIN_DIR/skills/frontend-design/"
    printf '{"name":"frontend-design","description":"Frontend design skill for UI/UX implementation","author":{"name":"Anthropic","email":"support@anthropic.com"}}' \
      > "$PLUGIN_DIR/.claude-plugin/plugin.json"
    rm -rf /tmp/anthropic-skills
    echo "frontend-design skill installed to plugin directory (effective next session)"
  else
    echo "Warning: Could not reach skills marketplace — frontend-design plugin unavailable as fallback"
  fi
else
  echo "frontend-design skill already present"
fi

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
