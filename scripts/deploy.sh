#!/usr/bin/env bash
# Nightly deploy: pull latest main and restart only when the SHA has changed.
# Reads DEPLOY_REPO_DIR (default: directory two levels above this script).
#
# Uses a marker file (.last-deployed-sha) to track the last *successfully
# completed* deploy rather than git HEAD. This means a deploy that fails
# mid-way (e.g. pip install fails) will be retried on the next run even
# though git HEAD has already been advanced by the git pull.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${DEPLOY_REPO_DIR:-$(dirname "$SCRIPT_DIR")}"

# Path to the venv pip; override via DEPLOY_VENV_PIP for testing.
VENV_PIP="${DEPLOY_VENV_PIP:-$REPO_DIR/backend/.venv/bin/pip}"

MARKER="$REPO_DIR/.last-deployed-sha"

cd "$REPO_DIR"

git fetch origin main

REMOTE_SHA="$(git rev-parse origin/main)"

DEPLOYED_SHA=""
if [ -f "$MARKER" ]; then
    DEPLOYED_SHA="$(cat "$MARKER")"
fi

if [ "$DEPLOYED_SHA" = "$REMOTE_SHA" ]; then
    echo "Already up to date ($REMOTE_SHA). Nothing to do."
    exit 0
fi

LOCAL_SHA="$(git rev-parse HEAD)"
echo "New commits detected ($LOCAL_SHA → $REMOTE_SHA). Deploying…"

git pull origin main

cd "$REPO_DIR/frontend"
npm run build

cd "$REPO_DIR"
"$VENV_PIP" install -e backend/

sudo systemctl restart family-dashboard

# Chromium is deliberately NOT restarted here. This runs at 02:00, inside
# the 22:00-06:30 display-off window — launching Chromium while the
# Wayland output is off leaves it permanently windowed (no live output to
# negotiate fullscreen against), every time, not intermittently. Chromium
# is instead restarted by scripts/restart-kiosk.sh, chained onto the
# crontab line that powers the display back on at 06:30, so it only ever
# starts once the output is confirmed live. See hardware.md, "Known issue:
# Chromium doesn't go fullscreen when launched while the display is off".

echo "$REMOTE_SHA" > "$MARKER"
echo "Deploy complete."
