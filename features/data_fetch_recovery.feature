Feature: Dashboard data fetch recovery

  All three data cards (travel, weather, calendar) must recover automatically
  when the backend becomes available after an initial failure. This handles the
  boot race condition where Chromium starts before the backend is ready.

  Scenario: travel error clears when a subsequent poll succeeds
    Given the travel API initially fails
    And then the travel API returns valid data
    When the retry interval fires
    Then the travel error message is gone
    And the travel data is displayed

  Scenario: weather card retries after an initial fetch failure
    Given the weather API initially fails
    And then the weather API returns valid data
    When the retry interval fires
    Then the weather error message is gone
    And the weather data is displayed

  Scenario: calendar card retries after an initial fetch failure
    Given the calendar API initially fails
    And then the calendar API returns valid data
    When the retry interval fires
    Then the calendar error message is gone
    And the calendar data is displayed
