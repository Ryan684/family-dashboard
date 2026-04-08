Feature: Weather per commuter destination
  The weather section shows one card per unique commuter end location.
  Office commuters see their work location's weather; WFH and off commuters
  see home weather. Duplicate locations are shown only once.
  Each card shows the current temperature and the day's forecast high — no
  multi-period hourly breakdown.

  Background:
    Given the home location is configured
    And two commuters are configured with their respective work locations

  Scenario: Office commuter sees their work location weather
    Given commuter "Ryan" has mode "office" today
    When the weather endpoint is requested
    Then the response contains a location entry named "Ryan's Office"
    And that entry includes a current temperature and a daily high

  Scenario: WFH commuter sees home weather
    Given commuter "Robyn" has mode "wfh" today
    When the weather endpoint is requested
    Then the response contains a location entry named "Home"

  Scenario: Off commuter sees home weather
    Given commuter "Ryan" has mode "off" today
    When the weather endpoint is requested
    Then the response contains a location entry named "Home"

  Scenario: Two commuters at different locations produce two cards
    Given commuter "Ryan" has mode "office" today
    And commuter "Robyn" has mode "office" today
    When the weather endpoint is requested
    Then the response contains two location entries

  Scenario: Two commuters both at home produce one card
    Given commuter "Ryan" has mode "wfh" today
    And commuter "Robyn" has mode "off" today
    When the weather endpoint is requested
    Then the response contains exactly one location entry

  Scenario: One office, one home produces two cards
    Given commuter "Ryan" has mode "office" today
    And commuter "Robyn" has mode "wfh" today
    When the weather endpoint is requested
    Then the response contains two location entries

  Scenario: Weather card frontend shows location name
    Given the API returns a locations list with one entry named "Ryan's Office"
    When the WeatherCard renders
    Then "Ryan's Office" is visible on screen

  Scenario: Weather card frontend shows current temperature
    Given the API returns a location with current temperature 15°C
    When the WeatherCard renders
    Then "15°C" is displayed

  Scenario: Weather card frontend shows daily high
    Given the API returns a location with daily high 19°C
    When the WeatherCard renders
    Then "High: 19°C" is displayed

  Scenario: Weather card frontend shows no hourly forecast slots
    Given the API returns a locations list
    When the WeatherCard renders
    Then no individual hourly forecast entries are visible

  Scenario: Weather card frontend renders one block per location
    Given the API returns two locations
    When the WeatherCard renders
    Then two location weather blocks are visible
