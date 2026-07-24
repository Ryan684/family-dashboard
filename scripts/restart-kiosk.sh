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
#
# Also called directly from ~/.config/labwc/autostart on every boot (see
# PI_SETUP.md, Part 14) — a trigger cron has no control over. A reboot can
# happen at any time, including inside the display-off window, so this
# script refuses to launch Chromium unless it's currently within the
# scheduled display-on window (default 06:30-22:00, matching the crontab
# entries in hardware.md) — otherwise it logs and exits, leaving Chromium
# untouched until the next scheduled wlopm --on + restart-kiosk.sh cron
# run. The cron-triggered call is always safely inside the window (it
# only ever fires right after wlopm --on), so this only matters for the
# autostart trigger.
set -euo pipefail

# KIOSK_NOW_HHMM overrides "now" for testing. All three are forced to
# base-10 with the "10#" prefix so a leading zero (e.g. "0630") is never
# misread as octal by shell arithmetic.
NOW_HHMM="${KIOSK_NOW_HHMM:-$(date +%H%M)}"
ON_HHMM="${KIOSK_ON_HHMM:-0630}"
OFF_HHMM="${KIOSK_OFF_HHMM:-2200}"

now_minutes=$(( 10#${NOW_HHMM:0:2} * 60 + 10#${NOW_HHMM:2:2} ))
on_minutes=$(( 10#${ON_HHMM:0:2} * 60 + 10#${ON_HHMM:2:2} ))
off_minutes=$(( 10#${OFF_HHMM:0:2} * 60 + 10#${OFF_HHMM:2:2} ))

if [ "$now_minutes" -lt "$on_minutes" ] || [ "$now_minutes" -ge "$off_minutes" ]; then
    echo "$(date -Iseconds) chromium-relaunch: skipped — display is scheduled off right now ($NOW_HHMM, on-window $ON_HHMM-$OFF_HHMM). The next scheduled wlopm --on + restart-kiosk.sh cron run will launch Chromium once the output is live."
    exit 0
fi

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
