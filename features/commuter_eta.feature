Feature: Commuter ETA display

  Each commuter card shows an estimated arrival time (ETA) derived from a
  configurable departure time stored in commute-schedule.json. If the current
  time is at or past the configured departure time, the ETA is calculated from
  the current time instead.

  # --- Backend: compute_eta ---

  Scenario: ETA is calculated from departure time when it has not yet elapsed
    Given the configured departure time is "07:30"
    And the current time is "07:00"
    And the primary route travel time is 1800 seconds
    When the ETA is computed
    Then the ETA is "08:00"

  Scenario: ETA is calculated from current time when departure time has elapsed
    Given the configured departure time is "07:30"
    And the current time is "07:45"
    And the primary route travel time is 1800 seconds
    When the ETA is computed
    Then the ETA is "08:15"

  Scenario: ETA is calculated from current time when departure time is exactly now
    Given the configured departure time is "07:30"
    And the current time is "07:30"
    And the primary route travel time is 1800 seconds
    When the ETA is computed
    Then the ETA is "08:00"

  Scenario: ETA is None when no departure time is configured
    Given no departure time is configured
    And the primary route travel time is 1800 seconds
    When the ETA is computed
    Then the ETA is None

  Scenario: ETA crosses midnight correctly
    Given the configured departure time is "23:50"
    And the current time is "23:00"
    And the primary route travel time is 1800 seconds
    When the ETA is computed
    Then the ETA is "00:20"

  # --- Backend: schedule resolution ---

  Scenario: departure_time is returned by the schedule resolver when configured
    Given a schedule where Monday has departure_time "07:30"
    When the commuter day is resolved for Monday
    Then the result includes departure_time "07:30"

  Scenario: departure_time is None when not set in the schedule
    Given a schedule where Monday has no departure_time
    When the commuter day is resolved for Monday
    Then the result departure_time is None

  # --- Backend: API response includes ETA ---

  Scenario: Commuter API response includes eta field when departure_time is configured
    Given the schedule has a departure_time for the active commuter today
    When the travel data is fetched
    Then the commuter result includes an eta value

  Scenario: Commuter API response has eta as None when no departure_time is configured
    Given the schedule has no departure_time for the active commuter today
    When the travel data is fetched
    Then the commuter result has eta as None

  # --- Frontend: ETA display ---

  Scenario: ETA is shown on the commuter card when provided
    Given a commuter with eta "08:15"
    When the TravelCard renders
    Then "ETA 08:15" is visible on the commuter card

  Scenario: ETA is not shown when eta is null
    Given a commuter with no eta
    When the TravelCard renders
    Then no ETA element is rendered

  Scenario: ETA is not shown when eta field is absent
    Given a commuter object without an eta field
    When the TravelCard renders
    Then no ETA element is rendered
