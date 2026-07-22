Feature: Nightly auto-deploy on Raspberry Pi
  A systemd timer fires at 02:00 each night and runs a deploy script.
  The script compares the last successfully deployed SHA (stored in a marker
  file) with origin/main: if they differ it pulls the latest code, rebuilds
  the frontend, reinstalls the backend via the backend venv, and restarts the
  family-dashboard service. If the marker SHA matches origin/main it exits
  quickly without touching the running service.

  Scenario: No action when already successfully deployed
    Given the deploy marker file records the current origin/main SHA
    When the deploy script runs
    Then git pull is not called
    And the npm build is not called
    And systemctl restart is not called
    And the script exits with code 0

  Scenario: Full deploy when new commits are available
    Given the local HEAD SHA differs from origin/main
    When the deploy script runs
    Then git pull is called
    And npm run build is called
    And pip install is called
    And systemctl restart family-dashboard is called
    And the script exits with code 0

  Scenario: Script aborts if git pull fails
    Given the local HEAD SHA differs from origin/main
    And git pull exits with a non-zero code
    When the deploy script runs
    Then npm run build is not called
    And systemctl restart is not called
    And the script exits with a non-zero code

  Scenario: Script aborts if npm build fails
    Given the local HEAD SHA differs from origin/main
    And npm run build exits with a non-zero code
    When the deploy script runs
    Then systemctl restart is not called
    And the script exits with a non-zero code

  Scenario: Chromium is restarted after a successful deploy
    Given the local HEAD SHA differs from origin/main
    When the deploy script runs
    Then pkill is called to stop Chromium
    And Chromium is relaunched in the background

  Scenario: Chromium is not restarted when already successfully deployed
    Given the deploy marker file records the current origin/main SHA
    When the deploy script runs
    Then pkill is not called

  Scenario: Relaunch waits for the old Chromium process to fully exit
    Given the local HEAD SHA differs from origin/main
    And the previous Chromium process takes a few seconds to exit after pkill
    When the deploy script runs
    Then the script polls for the old Chromium process to exit
    And Chromium is relaunched only after the old process is gone
    # A fixed sleep races a slow shutdown: if the old process is still
    # alive when the new one starts, Chromium's single-instance mechanism
    # forwards the URL to the dying process as an ordinary new window,
    # silently dropping --kiosk and leaving the dashboard windowed instead
    # of fullscreen.

  Scenario: Relaunch force-kills Chromium if it never exits cleanly
    Given the local HEAD SHA differs from origin/main
    And the previous Chromium process never exits after pkill
    When the deploy script runs
    Then the script force-kills the stuck Chromium process after a bounded wait
    And Chromium is still relaunched afterwards

  Scenario: Relaunch wipes the Chromium profile before starting
    Given the local HEAD SHA differs from origin/main
    And a stale Chromium profile directory exists from a previous run
    When the deploy script runs
    Then the stale profile directory is removed before Chromium is relaunched
    And Chromium is relaunched with a fresh --user-data-dir
    # A force-killed Chromium (SIGKILL, after the bounded wait above) leaves
    # an unclean shutdown. On next launch Chromium's session-restore silently
    # reopens the previous session's windows in their *saved* windowed state
    # — --disable-session-crashed-bubble only hides the restore prompt, it
    # doesn't disable the restore. A disposable profile wiped before every
    # launch means there is never anything to restore.

  Scenario: Backend pip install uses the virtual environment
    Given the local HEAD SHA differs from origin/main
    When the deploy script runs
    Then pip install is called via the backend virtual environment
    And system pip3 is not called

  Scenario: Marker file is written after a successful deploy
    Given the local HEAD SHA differs from origin/main
    When the deploy script runs
    Then a marker file is written containing the deployed SHA

  Scenario: A previously failed partial deploy is retried on the next run
    Given a previous deploy advanced local HEAD to origin/main but failed before completing
    And no deploy marker file exists
    When the deploy script runs
    Then git pull is called
    And npm run build is called
    And pip install is called
    And systemctl restart family-dashboard is called
    And the script exits with code 0

  Scenario: Relaunch logs whether the old Chromium process exited cleanly
    Given the local HEAD SHA differs from origin/main
    And the previous Chromium process takes a few seconds to exit after pkill
    When the deploy script runs
    Then the log records a timestamped line noting Chromium was relaunched after a clean exit
    # Chromium is known to sometimes fail to actually enter kiosk/fullscreen
    # presentation on launch even when --kiosk is passed and accepted (an
    # intermittent race in its Wayland startup handshake — see hardware.md,
    # "Known issue: Chromium sometimes doesn't go fullscreen on launch").
    # There's no cheap, reliable way to verify fullscreen state from this
    # script yet, so relaunches are logged with a timestamp and whether a
    # forced kill was needed, to build a correlatable history of when
    # restarts happened without reconstructing it from process start times
    # after the fact.

  Scenario: Relaunch logs when the old Chromium process had to be force-killed
    Given the local HEAD SHA differs from origin/main
    And the previous Chromium process never exits after pkill
    When the deploy script runs
    Then the log records a timestamped line noting Chromium required a forced kill before relaunching
