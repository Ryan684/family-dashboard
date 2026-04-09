Feature: Calendar backend
  The calendar backend fetches today's and tomorrow's events from the shared
  family iCloud calendar via CalDAV and returns them split into today/tomorrow lists.

  Scenario: Returns events split into today and tomorrow lists
    Given the CalDAV calendar has two events today and one event tomorrow
    When the dashboard calls GET /api/calendar
    Then the response status is 200
    And the "today" list has 2 events
    And the "tomorrow" list has 1 event

  Scenario: Timed events have ISO datetime start and all_day false
    Given the CalDAV calendar has a timed event at 09:00 today
    When the dashboard calls GET /api/calendar
    Then the event has a dateTime start value
    And the event has "all_day" set to false

  Scenario: All-day events have date-only start and all_day true
    Given the CalDAV calendar has an all-day event today
    When the dashboard calls GET /api/calendar
    Then the event has a date-only start value
    And the event has "all_day" set to true

  Scenario: Cancelled events are excluded from the response
    Given the CalDAV calendar has only a cancelled event
    When the dashboard calls GET /api/calendar
    Then the "today" list is empty
    And the "tomorrow" list is empty

  Scenario: No events returns empty lists
    Given the CalDAV calendar has no events
    When the dashboard calls GET /api/calendar
    Then the "today" list is empty
    And the "tomorrow" list is empty

  Scenario: Calendar not found returns empty lists
    Given the configured calendar name does not exist on the CalDAV server
    When the dashboard calls GET /api/calendar
    Then the "today" list is empty
    And the "tomorrow" list is empty
