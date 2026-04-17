Feature: Weather card frontend
  Background:
    Given the /api/weather endpoint is available

  Scenario: Loading state is shown while the API has not responded
    Given the API call has not yet resolved
    When the WeatherCard renders
    Then a loading indicator is visible

  Scenario: Location name is displayed
    Given the API returns a locations list with one entry named "Home"
    When the WeatherCard renders
    Then "Home" is visible on screen

  Scenario: Current temperature is displayed
    Given the API returns a location with current temperature 15°C
    When the WeatherCard renders
    Then the current temperature "15°C" is displayed

  Scenario: Weather description is displayed
    Given the API returns a location with description "Partly cloudy"
    When the WeatherCard renders
    Then the weather description "Partly cloudy" is displayed

  Scenario: Daily high is displayed
    Given the API returns a location with daily high 19°C
    When the WeatherCard renders
    Then "High: 19°C" is displayed

  Scenario: No hourly forecast entries are shown
    Given the API returns a locations list
    When the WeatherCard renders
    Then no individual hourly forecast entries are visible

  Scenario: Multiple location blocks are rendered
    Given the API returns two locations
    When the WeatherCard renders
    Then two location weather blocks are visible

  Scenario: Error state is shown when the API call fails
    Given the API call fails with a network error
    When the WeatherCard renders
    Then an error message is visible

  Scenario: Error state is shown when the API returns a non-ok status
    Given the API returns HTTP 500
    When the WeatherCard renders
    Then an error message is visible

  Scenario: Daily rainfall is displayed as "Rain: X.X mm (Y%)"
    Given the API returns a location with daily_rainfall total_mm 4.2 and probability_percent 60
    When the WeatherCard renders
    Then "Rain: 4.2 mm (60%)" is displayed

  Scenario: Rainfall row is hidden when daily_rainfall is absent
    Given the API returns a location without a daily_rainfall field
    When the WeatherCard renders
    Then no rainfall line is visible

  Scenario: Rainfall label uses "· X% chance" format
    Given the API returns a location with daily_rainfall probability_percent 60
    When the WeatherCard renders
    Then "60% chance" is visible on screen

  Scenario: Rain windows are displayed when present
    Given the API returns a location with rain_windows covering hours 8–10 and 14–16
    When the WeatherCard renders
    Then "8–10am, 2–4pm" is displayed

  Scenario: "all day" is shown when total rainy hours are 18 or more
    Given the API returns a location with rain_windows totalling 18 hours
    When the WeatherCard renders
    Then "all day" is displayed

  Scenario: Rain window row is hidden when rain_windows is empty
    Given the API returns a location with an empty rain_windows array
    When the WeatherCard renders
    Then no rain window row is visible

  Scenario: Rain window row is hidden when rain_windows is absent
    Given the API returns a location without a rain_windows field
    When the WeatherCard renders
    Then no rain window row is visible
