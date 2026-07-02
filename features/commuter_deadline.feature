Feature: Commuter arrival deadline and departure margin

  Each commuter can optionally configure an "arrive_by" time per day in
  commute-schedule.json (e.g. a 9am work start), alongside their existing
  departure_time. When both are configured, the backend computes the latest
  time you could leave home right now and still make it by that deadline
  given today's live travel time, plus how many minutes of slack remain
  against your planned departure time. This lets the dashboard warn you in
  concrete terms ("leave by 07:42") instead of a generic "leave early".

  # --- Backend: compute_departure_margin ---

  Scenario: Margin is positive when there is spare time before the deadline
    Given the configured departure time is "07:30"
    And the arrival deadline is "09:00"
    And the current time is "07:00"
    And the primary route travel time is 1800 seconds
    When the departure margin is computed
    Then the latest departure time is "08:30"
    And the margin is 60 minutes

  Scenario: Margin is exactly zero when departing at the latest safe moment
    Given the configured departure time is "07:30"
    And the arrival deadline is "08:00"
    And the current time is "07:00"
    And the primary route travel time is 1800 seconds
    When the departure margin is computed
    Then the latest departure time is "07:30"
    And the margin is 0 minutes

  Scenario: Margin is negative once the planned departure time has already elapsed
    Given the configured departure time is "07:30"
    And the arrival deadline is "08:00"
    And the current time is "07:45"
    And the primary route travel time is 1800 seconds
    When the departure margin is computed
    Then the latest departure time is "07:30"
    And the margin is -15 minutes

  Scenario: Margin is None when no arrival deadline is configured
    Given the configured departure time is "07:30"
    And no arrival deadline is configured
    And the primary route travel time is 1800 seconds
    When the departure margin is computed
    Then the departure margin is None

  Scenario: Margin is None when no departure time is configured
    Given no departure time is configured
    And the arrival deadline is "09:00"
    And the primary route travel time is 1800 seconds
    When the departure margin is computed
    Then the departure margin is None

  # --- Backend: schedule resolution ---

  Scenario: arrive_by is returned by the schedule resolver when configured
    Given a schedule where Monday has arrive_by "09:00"
    When the commuter day is resolved for Monday
    Then the result includes arrive_by "09:00"

  Scenario: arrive_by is None when not set in the schedule
    Given a schedule where Monday has no arrive_by
    When the commuter day is resolved for Monday
    Then the result arrive_by is None

  Scenario: arrive_by must be in HH:MM format like departure_time
    Given a schedule where Friday has arrive_by "9:00"
    When the schedule is loaded
    Then a configuration error is raised

  # --- Backend: API response includes deadline ---

  Scenario: Commuter API response includes a deadline object when arrive_by and departure_time are both configured
    Given the schedule has departure_time "07:30" and arrive_by "09:00" for the active commuter today
    When the travel data is fetched
    Then the commuter result includes a deadline object
    And the deadline object has an arrive_by value

  Scenario: Commuter API response has deadline as None when arrive_by is not configured
    Given the schedule has departure_time "07:30" and no arrive_by for the active commuter today
    When the travel data is fetched
    Then the commuter result has deadline as None

  # --- Frontend: AlertBanner deadline-aware message ---

  Scenario: Leave-early message references the deadline when a margin is available
    Given a home-to-work route has delay_colour "red"
    And the commuter has a deadline with latest_departure "07:42" and margin_minutes 8
    When the alert banner is rendered
    Then it displays a message advising the user to leave by "07:42"

  Scenario: Leave-early message warns when the margin is already negative
    Given a home-to-work route has delay_colour "red"
    And the commuter has a deadline with latest_departure "07:30" and margin_minutes -15
    When the alert banner is rendered
    Then it displays a message that the user is already 15 min behind schedule

  Scenario: Leave-early message falls back to the generic floor when no deadline is configured
    Given a home-to-work route has delay_colour "red" and delay_seconds 120
    And the commuter has no deadline configured
    When the alert banner is rendered
    Then it displays a message advising the user to leave 10 min early

  # --- Frontend: TravelCard margin display ---

  Scenario: Margin is shown next to ETA when a deadline is configured
    Given a commuter with a deadline of latest_departure "07:42" and margin_minutes 8
    When the TravelCard renders
    Then "Latest leave 07:42" is visible
    And "8 min to spare" is visible

  Scenario: Margin is shown as behind schedule when negative
    Given a commuter with a deadline of latest_departure "07:30" and margin_minutes -15
    When the TravelCard renders
    Then "15 min behind schedule" is visible

  Scenario: No deadline row shown when the commuter has no deadline configured
    Given a commuter with no deadline configured
    When the TravelCard renders
    Then no deadline element is rendered
