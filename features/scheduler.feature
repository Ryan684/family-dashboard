Feature: Background polling scheduler
  The scheduler polls travel, weather, and calendar APIs on a configurable
  interval within the morning window and caches the results. Routes serve
  fast local data from the cache; the stale flag indicates when live
  polling is inactive.

  Scenario: No API calls made outside the poll window
    Given the current time is outside the poll window
    When the scheduler runs a poll cycle
    Then no travel, weather, or calendar API calls are made

  Scenario: API calls made within the poll window
    Given the current time is within the poll window
    When the scheduler runs a poll cycle
    Then travel, weather, and calendar fetch functions are each called once

  Scenario: Poll cycle updates all router caches
    Given the current time is within the poll window
    When the scheduler polls successfully
    Then the travel router cache contains the fetched travel data
    And the weather router cache contains the fetched weather data
    And the calendar router cache contains the fetched calendar data

  Scenario: Travel endpoint serves cached data
    Given the travel cache contains route data
    And the current time is within the poll window
    When the dashboard calls GET /api/travel
    Then the response contains the cached route data
    And is_stale is false

  Scenario: Travel endpoint stale flag outside poll window
    Given the travel cache contains route data
    And the current time is outside the poll window
    When the dashboard calls GET /api/travel
    Then is_stale is true

  Scenario: Travel endpoint returns empty defaults with no cache
    Given the travel cache is empty
    When the dashboard calls GET /api/travel
    Then the response contains empty route lists
    And is_stale is true

  Scenario: Weather endpoint serves cached data
    Given the weather cache contains conditions and forecast data
    And the current time is within the poll window
    When the dashboard calls GET /api/weather
    Then the response contains the cached weather data
    And is_stale is false

  Scenario: Weather endpoint stale flag outside poll window
    Given the weather cache contains conditions and forecast data
    And the current time is outside the poll window
    When the dashboard calls GET /api/weather
    Then is_stale is true
