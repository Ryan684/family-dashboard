Feature: Kiosk Chromium restart, chained to the display-on cron
  Chromium must never be launched while the Pi's HDMI output is powered off
  (via `wlopm --off`) — its fullscreen request has no live output to
  negotiate against, so it falls back to an ordinary window and stays that
  way once the display powers back on. This isn't intermittent: it fails
  every time, because the nightly deploy used to restart Chromium at 02:00,
  squarely inside the 22:00-06:30 display-off window (see hardware.md,
  "Known issue: Chromium doesn't go fullscreen when launched while the
  display is off").

  scripts/restart-kiosk.sh kills and relaunches Chromium unconditionally
  whenever it's run. It carries no knowledge of deploys or SHAs — it is
  chained directly onto the crontab line that powers the display on at
  06:30 (`wlopm --on HDMI-A-1 && .../restart-kiosk.sh`), so Chromium only
  ever starts once the output is confirmed live. The nightly deploy
  (features/auto_deploy.feature) no longer touches Chromium at all.

  Scenario: Chromium is restarted every time the script runs
    When the kiosk restart script runs
    Then pkill is called to stop Chromium
    And Chromium is relaunched in the background

  Scenario: Relaunch waits for the old Chromium process to fully exit
    Given the previous Chromium process takes a few seconds to exit after pkill
    When the kiosk restart script runs
    Then the script polls for the old Chromium process to exit
    And Chromium is relaunched only after the old process is gone
    # A fixed sleep races a slow shutdown: if the old process is still
    # alive when the new one starts, Chromium's single-instance mechanism
    # forwards the URL to the dying process as an ordinary new window,
    # silently dropping --kiosk and leaving the dashboard windowed instead
    # of fullscreen.

  Scenario: Relaunch force-kills Chromium if it never exits cleanly
    Given the previous Chromium process never exits after pkill
    When the kiosk restart script runs
    Then the script force-kills the stuck Chromium process after a bounded wait
    And Chromium is still relaunched afterwards

  Scenario: Relaunch wipes the Chromium profile before starting
    Given a stale Chromium profile directory exists from a previous run
    When the kiosk restart script runs
    Then the stale profile directory is removed before Chromium is relaunched
    And Chromium is relaunched with a fresh --user-data-dir
    # A force-killed Chromium (SIGKILL, after the bounded wait above) leaves
    # an unclean shutdown. On next launch Chromium's session-restore silently
    # reopens the previous session's windows in their *saved* windowed state
    # — --disable-session-crashed-bubble only hides the restore prompt, it
    # doesn't disable the restore. A disposable profile wiped before every
    # launch means there is never anything to restore.

  Scenario: Relaunch logs whether the old Chromium process exited cleanly
    Given the previous Chromium process takes a few seconds to exit after pkill
    When the kiosk restart script runs
    Then the log records a timestamped line noting Chromium was relaunched after a clean exit
    # Retained from when this lived in deploy.sh: still useful for spotting
    # a stuck/crash-looping Chromium independent of the display-off launch
    # bug those forced kills were originally suspected to correlate with.

  Scenario: Relaunch logs when the old Chromium process had to be force-killed
    Given the previous Chromium process never exits after pkill
    When the kiosk restart script runs
    Then the log records a timestamped line noting Chromium required a forced kill before relaunching
