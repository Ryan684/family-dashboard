Feature: Nightly auto-deploy on Raspberry Pi
  A systemd timer fires at 02:00 each night and runs a deploy script.
  The script compares the last successfully deployed SHA (stored in a marker
  file) with origin/main: if they differ it pulls the latest code, rebuilds
  the frontend, reinstalls the backend via the backend venv, and restarts the
  family-dashboard service. If the marker SHA matches origin/main it exits
  quickly without touching the running service.

  Chromium is deliberately NOT restarted by this script — see
  features/kiosk_restart.feature. The display is powered off (via `wlopm`)
  from 22:00 to 06:30, and this deploy runs at 02:00, inside that window.
  Launching Chromium while the Wayland output is off leaves it permanently
  windowed instead of fullscreen, because its fullscreen request has no live
  output to negotiate against — this isn't a launch-timing race, it fails
  every time. Chromium is instead restarted by a separate script chained
  directly onto the 06:30 "display on" cron entry, so it only ever starts
  once the output is confirmed live (see hardware.md, "Known issue: Chromium
  doesn't go fullscreen when launched while the display is off").

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
    And npm ci is called
    And npm run build is called
    And pip install is called
    And systemctl restart family-dashboard is called
    And the script exits with code 0

  Scenario: Frontend dependencies are installed before the build
    Given the local HEAD SHA differs from origin/main
    When the deploy script runs
    Then npm ci is called before npm run build
    # Building against a node_modules left over from a previous deploy would
    # either fail confusingly or silently produce a build from the old
    # toolchain whenever the git pull brought a changed lockfile.

  Scenario: Script aborts if npm ci fails
    Given the local HEAD SHA differs from origin/main
    And npm ci exits with a non-zero code
    When the deploy script runs
    Then npm run build is not called
    And systemctl restart is not called
    And the script exits with a non-zero code

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

  Scenario: Backend pip install uses the virtual environment
    Given the local HEAD SHA differs from origin/main
    When the deploy script runs
    Then pip install is called via the backend virtual environment
    And system pip3 is not called

  Scenario: Backend dependencies are installed from the committed lockfile
    Given the local HEAD SHA differs from origin/main
    When the deploy script runs
    Then pip install -r backend/requirements.lock is called
    And the editable package install is called afterwards with --no-deps
    # Installing from the lockfile means a deploy gets the exact versions that
    # were tested, instead of whatever PyPI happens to resolve to that night.

  Scenario: Script aborts if the locked dependency install fails
    Given the local HEAD SHA differs from origin/main
    And the lockfile install exits with a non-zero code
    When the deploy script runs
    Then systemctl restart is not called
    And the script exits with a non-zero code

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
