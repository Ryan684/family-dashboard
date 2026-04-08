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
