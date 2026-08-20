Feature: Tomorrow forecast card frontend
  The TomorrowCard occupies the column freed when the travel section is hidden,
  showing tomorrow's forecast beside today's so the two read as a comparison.

  It is deliberately quieter than the weather card: a 48px high rather than an
  88px current temperature, and no live conditions at all. Tomorrow is a
  forecast, not a fact, and the weekday in its heading is what stops two columns
  of temperatures reading as a duplication bug.

  Background:
    Given the /api/weather endpoint is available

  Scenario: Loading state is shown while the API has not responded
    Given the API call has not yet resolved
    When the TomorrowCard renders
    Then a loading indicator is visible

  Scenario: The heading names tomorrow's weekday
    Given the API returns a tomorrow block with weekday "Wednesday"
    When the TomorrowCard renders
    Then "Wednesday" is visible on screen

  Scenario: Location name is displayed
    Given the API returns a tomorrow location named "Home"
    When the TomorrowCard renders
    Then "Home" is visible on screen

  Scenario: The daily high is displayed as the headline figure
    Given the API returns a tomorrow location with daily high 17°C
    When the TomorrowCard renders
    Then "17°C" is displayed

  Scenario: Weather description is displayed
    Given the API returns a tomorrow location with description "Light rain"
    When the TomorrowCard renders
    Then the weather description "Light rain" is displayed

  Scenario: No current temperature is rendered
    Given the API returns today's locations with current temperature 8°C
    And a tomorrow location with daily high 17°C
    When the TomorrowCard renders
    Then "8°C" is not visible on screen

  Scenario: Daily rainfall is displayed
    Given the API returns a tomorrow location with daily_rainfall total_mm 3.1 and probability_percent 70
    When the TomorrowCard renders
    Then "Rain: 3.1 mm · 70% chance" is displayed

  Scenario: Rainfall row is hidden when total_mm is zero
    Given the API returns a tomorrow location with daily_rainfall total_mm 0
    When the TomorrowCard renders
    Then no rainfall line is visible

  Scenario: Rainfall row is hidden when daily_rainfall is absent
    Given the API returns a tomorrow location without a daily_rainfall field
    When the TomorrowCard renders
    Then no rainfall line is visible

  Scenario: Rain windows are displayed when present
    Given the API returns a tomorrow location with rain_windows covering hours 14–17
    When the TomorrowCard renders
    Then "2–5pm" is displayed

  Scenario: Rain window row is hidden when rain_windows is empty
    Given the API returns a tomorrow location with an empty rain_windows array
    When the TomorrowCard renders
    Then no rain window row is visible

  Scenario: One block is rendered per tomorrow location
    Given the API returns two tomorrow locations
    When the TomorrowCard renders
    Then two tomorrow location blocks are visible

  Scenario: A payload without a tomorrow block shows an unavailable message
    Given the API response has no tomorrow key
    When the TomorrowCard renders
    Then a "Tomorrow unavailable" status is visible

  Scenario: An empty tomorrow locations list shows an unavailable message
    Given the API returns a tomorrow block with no locations
    When the TomorrowCard renders
    Then a "Tomorrow unavailable" status is visible

  Scenario: Error state is shown when the API call fails
    Given the API call fails with a network error
    When the TomorrowCard renders
    Then an error message is visible

  Scenario: Error state is shown when the API returns a non-ok status
    Given the API returns HTTP 500
    When the TomorrowCard renders
    Then an error message is visible

  Scenario: No stale indicator is shown, even when the data is cached
    Given the API response has is_stale true
    When the TomorrowCard renders
    Then no stale data warning is visible

  # The weather card, which always renders beside this one and reads the same
  # endpoint, already carries the indicator; a second one is duplication. It also
  # does not fit — heading plus tag overflow this column and wrap to two lines,
  # dropping the first location block below its neighbour and breaking the shared
  # baseline that makes the two columns read as a comparison.
