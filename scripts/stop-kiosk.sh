#!/usr/bin/env bash
# Stop Chromium when the display powers off.
#
# Chained onto the crontab line that runs `wlopm --off HDMI-A-1` at 22:00 (see
# hardware.md), the mirror image of the `wlopm --on` + restart-kiosk.sh line at
# 06:30.
#
# Why: from 22:00 to 06:30 the Wayland output is dark and nobody is looking at it,
# but Chromium still holds roughly half a gigabyte resident. The Pi is a 4GB Pi 5
# now shared with the budget planner, and the nightly maintenance window sits
# inside those hours — the family-dashboard deploy at 02:00 (`npm ci` + `vite
# build`, the largest transient memory consumer on the box) and the budget-planner
# backup at 03:30. Freeing Chromium's memory for the whole window keeps a build
# spike from pushing the kernel into an OOM kill, which would otherwise pick its
# victim by badness score — most likely Chromium itself or one of the two backends.
#
# This deliberately does NOT relaunch anything. Chromium must never be started
# while the output is powered off: its fullscreen request has no live output to
# negotiate against and it comes back as an ordinary window, permanently (see
# hardware.md, "Chromium doesn't go fullscreen when launched while the display is
# off"). The only launch path is restart-kiosk.sh, chained to `wlopm --on` at
# 06:30, which additionally refuses to run outside the display-on window. So a
# stop here is always recovered by the next morning's cron run, and never races a
# relaunch.
#
# Consequence worth knowing: if you power the display on by hand overnight you
# will find no browser running. To get it back outside the window:
#   KIOSK_OFF_HHMM=2359 scripts/restart-kiosk.sh
set -euo pipefail

if ! pgrep -f chromium >/dev/null 2>&1; then
    echo "$(date -Iseconds) chromium-stop: nothing running, nothing to stop."
    exit 0
fi

pkill -f chromium || true

# pkill only sends SIGTERM. Wait for the process to actually exit — the whole
# point is to release its memory before the 02:00 deploy, and a hung process that
# ignored the TERM would release nothing. restart-kiosk.sh wipes the disposable
# --user-data-dir profile before every launch, so a SIGKILL here cannot leave
# session-restore state behind to break tomorrow's fullscreen launch.
for _ in $(seq 1 10); do
    pgrep -f chromium >/dev/null 2>&1 || break
    sleep 1
done

if pgrep -f chromium >/dev/null 2>&1; then
    pkill -9 -f chromium >/dev/null 2>&1 || true
    echo "$(date -Iseconds) chromium-stop: required a forced kill (SIGKILL) to release memory."
else
    echo "$(date -Iseconds) chromium-stop: exited cleanly, memory released for the night."
fi
