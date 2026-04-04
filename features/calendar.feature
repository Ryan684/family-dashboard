Feature: Calendar backend
  The calendar backend fetches today's and tomorrow's events from the shared
  family Google Calendar and returns them in a normalised format.

  Scenario: Returns events for today and tomorrow
    Given the Google Calendar API returns two events today and one event tomorrow
    When the dashboard calls GET /api/calendar
    Then the response status is 200
    And the response body contains an "events" list with three entries

  Scenario: Timed events carry dateTime values and are not flagged as all-day
    Given the Google Calendar API returns a timed event at 09:00 today
    When the dashboard calls GET /api/calendar
    Then the event has a dateTime start value
    And the event has "all_day" set to false

  Scenario: All-day events carry date values and are flagged as all-day
    Given the Google Calendar API returns an all-day event today
    When the dashboard calls GET /api/calendar
    Then the event has a date-only start value
    And the event has "all_day" set to true

  Scenario: Cancelled events are excluded from the response
    Given the Google Calendar API returns only a cancelled event
    When the dashboard calls GET /api/calendar
    Then the response body contains an empty "events" list

  Scenario: No events returns an empty list
    Given the Google Calendar API returns no events
    When the dashboard calls GET /api/calendar
    Then the response body contains an empty "events" list
