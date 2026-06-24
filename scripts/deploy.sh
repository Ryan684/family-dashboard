#!/usr/bin/env bash
# Nightly deploy: pull latest main and restart only when the SHA has changed.
# Reads DEPLOY_REPO_DIR (default: directory two levels above this script).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${DEPLOY_REPO_DIR:-$(dirname "$SCRIPT_DIR")}"

cd "$REPO_DIR"

git fetch origin main

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse origin/main)"

if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
    echo "Already up to date ($LOCAL_SHA). Nothing to do."
    exit 0
fi

echo "New commits detected ($LOCAL_SHA → $REMOTE_SHA). Deploying…"

git pull origin main

cd "$REPO_DIR/frontend"
npm run build

cd "$REPO_DIR"
pip3 install -e backend/

sudo systemctl restart family-dashboard

pkill -f chromium || true
sleep 5
setsid bash -c 'XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 chromium --ozone-platform=wayland --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --password-store=basic http://localhost:8000 >/dev/null 2>&1' &

echo "Deploy complete."
