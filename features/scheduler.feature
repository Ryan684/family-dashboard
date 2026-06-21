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

  Scenario: Weather endpoint stale flag outside weather poll window
    Given the weather cache contains conditions and forecast data
    And the current time is outside the weather poll window
    When the dashboard calls GET /api/weather
    Then is_stale is true

  Scenario: Weather continues to poll after the travel window closes
    Given the current time is after the travel window end but before the weather window end
    When the scheduler runs a poll cycle
    Then the weather fetch function is called
    But the travel and calendar fetch functions are not called

  Scenario: Weather endpoint is not stale between travel window end and weather window end
    Given the weather cache contains conditions and forecast data
    And the current time is after the travel window end but before the weather window end
    When the dashboard calls GET /api/weather
    Then is_stale is false

  Scenario: One fetcher failing does not skip remaining fetchers
    Given the weather fetcher raises a timeout error
    When poll_once is called
    Then the travel cache is updated with the travel data
    And the calendar cache is updated with the calendar data
    And the weather cache retains its previous value

  Scenario: Scheduler loop continues after a failed poll cycle
    Given the poll cycle raises an exception on the first call
    When the scheduler runs two cycles
    Then the scheduler completes both cycles without crashing

  Scenario: All caches primed on startup regardless of poll window
    Given the current time is outside the poll window
    When the scheduler starts
    Then travel, weather, and calendar are each fetched once immediately

  Scenario: Calendar not re-polled until its interval has elapsed
    Given the current time is within the poll window
    And the calendar was fetched at startup
    And the calendar poll interval has not elapsed
    When the scheduler runs a poll cycle
    Then the calendar fetch function is not called
    And the travel and weather fetch functions are called

  Scenario: Calendar re-fetched once its interval has elapsed
    Given the current time is within the poll window
    And the calendar poll interval has elapsed since the last fetch
    When the scheduler runs a poll cycle
    Then the calendar fetch function is called

  Scenario: WEATHER_POLL_WINDOW_END is required in environment
    Given WEATHER_POLL_WINDOW_END is absent from the environment
    When settings are loaded
    Then a configuration error is raised

  Scenario: CALENDAR_POLL_INTERVAL_SECONDS is required in environment
    Given CALENDAR_POLL_INTERVAL_SECONDS is absent from the environment
    When settings are loaded
    Then a configuration error is raised
