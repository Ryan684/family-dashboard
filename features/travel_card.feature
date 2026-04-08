Feature: Travel card frontend

  Background:
    Given the /api/travel endpoint is available

  Scenario: Route description is shown on each card
    Given a route with description "via A3 and M25"
    When the TravelCard renders
    Then the text "via A3 and M25" is visible

  Scenario: Green colour state rendered for low-delay route
    Given a route with delay_colour "green"
    When the TravelCard renders
    Then the route card has a green colour indicator

  Scenario: Amber colour state rendered for moderate-delay route
    Given a route with delay_colour "amber"
    When the TravelCard renders
    Then the route card has an amber colour indicator

  Scenario: Red colour state rendered for high-delay route
    Given a route with delay_colour "red"
    When the TravelCard renders
    Then the route card has a red colour indicator

  Scenario: Incident list shown only when incidents are present
    Given the API returns 1 incident with description "Roadworks on A3"
    When the TravelCard renders
    Then the incident "Roadworks on A3" is visible

  Scenario: Incident list not shown when no incidents
    Given the API returns 0 incidents
    When the TravelCard renders
    Then no incident section is rendered

  Scenario: Stale data indicator shown when is_stale is true
    Given the API response has is_stale true
    When the TravelCard renders
    Then a stale data warning is visible

  Scenario: Travel time displayed in minutes
    Given a route with travel_time_seconds 2700
    When the TravelCard renders
    Then "45 min" is visible on the route card

  Scenario: Loading state shown while data is fetching
    Given the API has not yet responded
    When the TravelCard renders
    Then a loading indicator is visible

  Scenario: Error state shown when the API call fails
    Given the API returns an error
    When the TravelCard renders
    Then an error message is visible

  Scenario: Route map is shown when encoded polyline is present
    Given a route with an encoded polyline
    When the TravelCard renders
    Then a route map container is visible for that route

  Scenario: Route map is not shown when encoded polyline is absent
    Given a route without an encoded polyline
    When the TravelCard renders
    Then no route map container is rendered
