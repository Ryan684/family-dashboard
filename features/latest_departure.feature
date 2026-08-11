Feature: Latest departure time

  Each commuter day may configure an arrive_by time in commute-schedule.json
  alongside departure_time. During commute polling the live travel time for the
  primary route is subtracted from arrive_by to give the latest time the
  commuter can leave and still arrive on time. The result is shown on the
  commuter card directly below the intended departure time.

  The latest departure is floored to the whole minute so following it never
  makes the commuter late: 08:00 minus 56m30s gives 07:03, not 07:04.

  # --- Backend: compute_latest_departure ---

  Scenario: Latest departure is arrive_by minus the travel time
    Given the configured arrive_by is "08:00"
    And the primary route travel time is 1800 seconds
    When the latest departure is computed
    Then the latest departure is "07:30"

  Scenario: Part-minute travel time is floored to the earlier minute
    Given the configured arrive_by is "08:00"
    And the primary route travel time is 3390 seconds
    When the latest departure is computed
    Then the latest departure is "07:03"

  Scenario: Latest departure is the arrive_by time when travel time is zero
    Given the configured arrive_by is "08:00"
    And the primary route travel time is 0 seconds
    When the latest departure is computed
    Then the latest departure is "08:00"

  Scenario: Latest departure is None when no arrive_by is configured
    Given no arrive_by is configured
    And the primary route travel time is 1800 seconds
    When the latest departure is computed
    Then the latest departure is None

  Scenario: Latest departure wraps backwards across midnight
    Given the configured arrive_by is "00:20"
    And the primary route travel time is 1800 seconds
    When the latest departure is computed
    Then the latest departure is "23:50"

  Scenario: Latest departure may fall before the intended departure time
    Given the configured arrive_by is "08:00"
    And the primary route travel time is 4200 seconds
    When the latest departure is computed
    Then the latest departure is "06:50"

  # --- Backend: schedule validation ---

  Scenario: valid HH:MM arrive_by is accepted
    Given a commute schedule where a commuter has arrive_by "08:00"
    When the schedule is loaded
    Then no error is raised

  Scenario: single-digit hour arrive_by is rejected
    Given a commute schedule where a commuter has arrive_by "8:00"
    When the schedule is loaded
    Then a ValueError is raised

  Scenario: absent arrive_by is accepted
    Given a commute schedule where a commuter has no arrive_by set
    When the schedule is loaded
    Then no error is raised

  Scenario: arrive_by error message identifies the commuter, day, and bad value
    Given a commute schedule where a commuter has arrive_by "8:00"
    When the schedule is loaded
    Then the error message contains the commuter name, the weekday, and "8:00"

  # --- Backend: schedule resolution ---

  Scenario: arrive_by is returned by the schedule resolver when configured
    Given a schedule where Monday has arrive_by "08:00"
    When the commuter day is resolved for Monday
    Then the result includes arrive_by "08:00"

  Scenario: arrive_by is None when not set in the schedule
    Given a schedule where Monday has no arrive_by
    When the commuter day is resolved for Monday
    Then the result arrive_by is None

  # --- Backend: API response includes latest departure ---

  Scenario: Commuter API response includes latest_departure when arrive_by is configured
    Given the schedule has an arrive_by for the active commuter today
    When the travel data is fetched
    Then the commuter result includes a latest_departure value

  Scenario: Commuter API response has latest_departure as None when no arrive_by is configured
    Given the schedule has no arrive_by for the active commuter today
    When the travel data is fetched
    Then the commuter result has latest_departure as None

  # --- Frontend: latest departure display ---

  Scenario: Latest departure is shown on the commuter card when provided
    Given a commuter with latest_departure "07:03"
    When the TravelCard renders
    Then "Leave by 07:03" is visible on the commuter card

  Scenario: Latest departure is shown below the intended departure time
    Given a commuter with departure_time "07:10" and latest_departure "07:03"
    When the TravelCard renders
    Then the latest departure element appears after the departure time element

  Scenario: Latest departure is not shown when latest_departure is null
    Given a commuter with no latest_departure
    When the TravelCard renders
    Then no latest departure element is rendered

  Scenario: Latest departure is not shown when the latest_departure field is absent
    Given a commuter object without a latest_departure field
    When the TravelCard renders
    Then no latest departure element is rendered

  Scenario: Latest departure is shown even when no departure time is configured
    Given a commuter with no departure_time and latest_departure "07:03"
    When the TravelCard renders
    Then "Leave by 07:03" is visible on the commuter card
