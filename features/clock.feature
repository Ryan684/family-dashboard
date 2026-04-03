Feature: Clock card
  The clock card displays the current time and date, readable at a glance from across the room.
  It reads the browser's local time — no backend endpoint required.

  Scenario: Displays current time in 24-hour format
    Given the current time is 14:05
    When the clock card renders
    Then the time is displayed as "14:05"

  Scenario: Displays single-digit minutes with a leading zero
    Given the current time is 09:07
    When the clock card renders
    Then the time is displayed as "09:07"

  Scenario: Displays current date as weekday, day number, and month name
    Given the current date is Thursday 3 April 2025
    When the clock card renders
    Then the date is displayed as "Thursday 3 April"

  Scenario: Clock updates every minute
    Given the clock card is rendered at 08:59
    When one minute elapses
    Then the time updates to "09:00"
