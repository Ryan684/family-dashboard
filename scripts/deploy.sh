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
# `npm ci` before building: the build alone would happily link against a stale
# node_modules from a previous deploy, so any lockfile change pulled by the git
# pull above would either fail confusingly or silently build the old toolchain.
npm ci
# Cap the V8 heap. Node sizes its default old-space from total system memory,
# which on this 4GB Pi 5 lands near 2GB — more than the box can spare now that it
# also runs the budget planner's backend. This build is 13 source files and will
# never approach 1GB, so the cap costs nothing and stops a runaway build from
# reaching the point where the kernel OOM-kills a live service instead. The
# 22:00 stop-kiosk.sh run has already freed Chromium's memory by the time this
# runs at 02:00 — see MemoryHigh in family-dashboard-deploy.service.
NODE_OPTIONS="--max-old-space-size=1024" npm run build

cd "$REPO_DIR"
# Dependencies come from the committed lockfile so a deploy installs the exact
# versions that were tested, rather than whatever PyPI resolves to that night.
# The package itself is then installed --no-deps, since the lockfile has already
# provided everything it needs.
"$VENV_PIP" install -r backend/requirements.lock
"$VENV_PIP" install -e backend/ --no-deps

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
