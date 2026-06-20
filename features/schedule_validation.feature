Feature: Commute schedule departure_time validation

  departure_time values in commute-schedule.json must follow HH:MM format
  (two-digit hour, colon, two-digit minute). An invalid value causes the
  schedule to fail at load time with a clear error message, which surfaces
  in the service logs rather than silently corrupting cached travel data.

  Scenario: valid HH:MM departure_time is accepted
    Given a commute schedule where a commuter has departure_time "07:25"
    When the schedule is loaded
    Then no error is raised

  Scenario: single-digit hour is rejected
    Given a commute schedule where a commuter has departure_time "7:25"
    When the schedule is loaded
    Then a ValueError is raised

  Scenario: absent departure_time is accepted
    Given a commute schedule where a commuter has no departure_time set
    When the schedule is loaded
    Then no error is raised

  Scenario: error message identifies the commuter, day, and bad value
    Given a commute schedule where a commuter has departure_time "7:25"
    When the schedule is loaded
    Then the error message contains the commuter name, the weekday, and "7:25"
