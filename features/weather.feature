Feature: Weather card backend
  Background:
    Given the home location is configured with a latitude and longitude

  Scenario: Current conditions are returned for the home location
    Given Open-Meteo returns current weather data for home
    When the dashboard requests the weather endpoint
    Then the response contains temperature, apparent temperature, weather description, wind speed, and humidity

  Scenario: Short forecast is returned for the next 6 hours
    Given Open-Meteo returns hourly forecast data for home
    When the dashboard requests the weather endpoint
    Then the response contains a forecast list with 6 hourly entries
    And each forecast entry contains a time, temperature, weather description, and precipitation probability

  Scenario: WMO weather code 0 maps to "Clear sky"
    Given a WMO weather code of 0
    When the code is mapped to a description
    Then the description is "Clear sky"

  Scenario: WMO weather code 61 maps to "Light rain"
    Given a WMO weather code of 61
    When the code is mapped to a description
    Then the description is "Light rain"

  Scenario: Unknown WMO weather code falls back to "Unknown"
    Given a WMO weather code not in the known set
    When the code is mapped to a description
    Then the description is "Unknown"

  Scenario: Forecast starts from the current hour
    Given the current time matches an entry in the hourly forecast
    When the forecast is parsed
    Then the first forecast entry matches the current hour
