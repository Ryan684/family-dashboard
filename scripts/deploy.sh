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

echo "Deploy complete."
