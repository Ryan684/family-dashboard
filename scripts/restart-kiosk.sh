#!/usr/bin/env bash
# Restart Chromium in kiosk mode. Chained directly onto the crontab line
# that powers the display on (`wlopm --on HDMI-A-1 && .../restart-kiosk.sh`
# — see hardware.md) so Chromium only ever starts once the Wayland output
# is confirmed live.
#
# Chromium must never be launched while the output is off: its fullscreen
# request has no live output to negotiate against, so it falls back to an
# ordinary window and stays that way once the display powers back on. This
# used to run from deploy.sh at 02:00 — squarely inside the 22:00-06:30
# display-off window — which failed every single time, not intermittently
# (see hardware.md, "Known issue: Chromium doesn't go fullscreen when
# launched while the display is off").
#
# Unlike deploy.sh, this script carries no SHA/marker-file gating — it
# restarts Chromium unconditionally every time it's invoked.
set -euo pipefail

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

# Recorded purely for the log line below — pkill -9 itself is unconditional
# and harmless either way (a no-op against an already-exited process).
CHROMIUM_FORCE_KILLED=0
pgrep -f chromium >/dev/null 2>&1 && CHROMIUM_FORCE_KILLED=1
pkill -9 -f chromium >/dev/null 2>&1 || true

# Wipe the profile before every launch. If the process above needed the
# SIGKILL fallback, Chromium saw that as a crash and will otherwise silently
# restore the previous session's windows in their *saved* windowed state on
# next launch — --disable-session-crashed-bubble only hides the restore
# prompt, it doesn't disable the restore itself. A disposable profile means
# there is never a previous session to restore.
CHROME_PROFILE_DIR="${KIOSK_CHROME_PROFILE_DIR:-$HOME/.cache/chromium-kiosk}"
rm -rf "$CHROME_PROFILE_DIR"

setsid bash -c "XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 chromium --ozone-platform=wayland --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --password-store=basic --user-data-dir='$CHROME_PROFILE_DIR' http://localhost:8000 >/dev/null 2>&1" &

if [ "$CHROMIUM_FORCE_KILLED" = "1" ]; then
    echo "$(date -Iseconds) chromium-relaunch: previous process required a forced kill (SIGKILL) before relaunching."
else
    echo "$(date -Iseconds) chromium-relaunch: previous process exited cleanly."
fi
