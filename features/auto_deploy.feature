Feature: Nightly auto-deploy on Raspberry Pi
  A systemd timer fires at 02:00 each night and runs a deploy script.
  The script compares the local git SHA with origin/main: if they differ
  it pulls the latest code, rebuilds the frontend, reinstalls the backend,
  and restarts the family-dashboard service. If they match it exits quickly
  without touching the running service.

  Scenario: No action when already up to date
    Given the local HEAD SHA matches origin/main
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
