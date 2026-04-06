Feature: Travel backend — routes and incidents

  Background:
    Given the routing API is available

  Scenario: Route description extracted from significant road names
    Given a route with guidance instructions containing roads "A3", "minor road", "M25", "local street"
    When the route description is built
    Then the description is "via A3 and M25"

  Scenario: Route description with three significant roads
    Given a route with guidance instructions containing roads "A3", "M25", "A316"
    When the route description is built
    Then the description is "via A3, M25 and A316"

  Scenario: Route description with no significant roads
    Given a route with guidance instructions containing no motorways or A-roads
    When the route description is built
    Then the description is ""

  Scenario: Delay colour is green when delay is below 10 percent
    Given a route with no-traffic time 1000 seconds and traffic delay 99 seconds
    When the delay colour is classified
    Then the colour is "green"

  Scenario: Delay colour is amber when delay is exactly 10 percent
    Given a route with no-traffic time 1000 seconds and traffic delay 100 seconds
    When the delay colour is classified
    Then the colour is "amber"

  Scenario: Delay colour is amber when delay is between 10 and 25 percent
    Given a route with no-traffic time 1000 seconds and traffic delay 200 seconds
    When the delay colour is classified
    Then the colour is "amber"

  Scenario: Delay colour is amber when delay is exactly 25 percent
    Given a route with no-traffic time 1000 seconds and traffic delay 250 seconds
    When the delay colour is classified
    Then the colour is "amber"

  Scenario: Delay colour is red when delay exceeds 25 percent
    Given a route with no-traffic time 1000 seconds and traffic delay 251 seconds
    When the delay colour is classified
    Then the colour is "red"

  Scenario: Incident warnings returned when incidents are present
    Given the incident data contains 2 incidents of significant severity
    When the travel endpoint is called
    Then the response contains 2 incidents
    And each incident has type, description, and road fields

  Scenario: No incident warnings when none are present
    Given the incident data contains no incidents
    When the travel endpoint is called
    Then the response contains 0 incidents

  Scenario: Minor incidents are filtered out
    Given the incident data contains an incident with magnitudeOfDelay 1
    When incidents are parsed
    Then the incident is excluded from the result

  Scenario: Bounding box is calculated from route polylines
    Given route polylines spanning lat 51.4 to 51.6 and lon -0.3 to 0.1
    When the bounding box is calculated
    Then the bounding box is min_lat=51.4, max_lat=51.6, min_lon=-0.3, max_lon=0.1

  Scenario: Bounding box is expanded by 0.02 degrees
    Given a bounding box min_lat=51.4, max_lat=51.6, min_lon=-0.3, max_lon=0.1
    When the bounding box is expanded
    Then the expanded box is min_lat=51.38, max_lat=51.62, min_lon=-0.32, max_lon=0.12

  Scenario: Response is marked stale when outside poll window
    Given the current time is outside the configured poll window
    When the travel endpoint is called with a cached result
    Then the response field is_stale is true

  Scenario: Response is not stale when within poll window
    Given the current time is within the configured poll window
    When the travel endpoint is called
    Then the response field is_stale is false
