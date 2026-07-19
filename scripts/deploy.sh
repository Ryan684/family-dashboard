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

pkill -f chromium || true

# pkill only sends SIGTERM; wait for the process to actually exit before
# relaunching. A relaunch that races a still-dying process gets silently
# absorbed into it via Chromium's single-instance IPC (the new URL opens
# as an ordinary window in the old process instead of a fresh --kiosk one),
# leaving the dashboard windowed instead of fullscreen.
for _ in $(seq 1 10); do
    pgrep -f chromium >/dev/null 2>&1 || break
    sleep 1
done
pkill -9 -f chromium >/dev/null 2>&1 || true

# Wipe the profile before every launch. If the process above needed the
# SIGKILL fallback, Chromium saw that as a crash and will otherwise silently
# restore the previous session's windows in their *saved* windowed state on
# next launch — --disable-session-crashed-bubble only hides the restore
# prompt, it doesn't disable the restore itself. A disposable profile means
# there is never a previous session to restore.
CHROME_PROFILE_DIR="${DEPLOY_CHROME_PROFILE_DIR:-$HOME/.cache/chromium-kiosk}"
rm -rf "$CHROME_PROFILE_DIR"

setsid bash -c "XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 chromium --ozone-platform=wayland --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --password-store=basic --user-data-dir='$CHROME_PROFILE_DIR' http://localhost:8000 >/dev/null 2>&1" &

echo "$REMOTE_SHA" > "$MARKER"
echo "Deploy complete."
