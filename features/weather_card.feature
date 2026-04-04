Feature: Weather card frontend
  Background:
    Given the /api/weather endpoint is available

  Scenario: Loading state is shown while the API has not responded
    Given the API call has not yet resolved
    When the WeatherCard renders
    Then a loading indicator is visible

  Scenario: Current temperature is displayed
    Given the API returns current weather with temperature 15°C
    When the WeatherCard renders
    Then the current temperature "15°C" is displayed

  Scenario: Weather description is displayed
    Given the API returns current weather with description "Partly cloudy"
    When the WeatherCard renders
    Then the weather description "Partly cloudy" is displayed

  Scenario: Apparent temperature is displayed
    Given the API returns apparent temperature 12°C
    When the WeatherCard renders
    Then "Feels like 12°C" is displayed

  Scenario: Wind speed and humidity are displayed
    Given the API returns wind speed 18 km/h and humidity 72%
    When the WeatherCard renders
    Then "18 km/h" is displayed
    And "72%" is displayed

  Scenario: Hourly forecast entries are displayed
    Given the API returns a 6-entry hourly forecast
    When the WeatherCard renders
    Then 6 forecast entries are visible

  Scenario: Each forecast entry shows time, temperature, and weather
    Given the API returns a forecast entry at "09:00" with temperature 14°C and description "Clear sky"
    When the WeatherCard renders
    Then "09:00" is displayed
    And "14°C" is displayed in the forecast
    And "Clear sky" is displayed in the forecast

  Scenario: Precipitation probability is displayed for a forecast entry
    Given the API returns a forecast entry with precipitation probability 40%
    When the WeatherCard renders
    Then "40%" is displayed in the forecast

  Scenario: Error state is shown when the API call fails
    Given the API call fails with a network error
    When the WeatherCard renders
    Then an error message is visible

  Scenario: Error state is shown when the API returns a non-ok status
    Given the API returns HTTP 500
    When the WeatherCard renders
    Then an error message is visible
