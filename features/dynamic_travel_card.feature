Feature: Dynamic travel card frontend — per-commuter cards and grid reflow

  Background:
    Given the /api/travel endpoint returns the per-commuter response shape

  # --- Card presence ---

  Scenario: Two commuter cards are shown when both commuters are active
    Given the API returns 2 commuter entries for "Ryan" and "Emily"
    When the dashboard renders
    Then 2 travel cards are visible
    And a card with header "Ryan" is visible
    And a card with header "Emily" is visible

  Scenario: One commuter card is shown when only one commuter is active
    Given the API returns 1 commuter entry for "Ryan"
    When the dashboard renders
    Then 1 travel card is visible
    And a card with header "Ryan" is visible

  Scenario: No travel cards are shown when commuters array is empty
    Given the API returns 0 commuter entries
    When the dashboard renders
    Then 0 travel cards are visible
    And the travel section is not rendered

  # --- Card content ---

  Scenario: Commuter name is shown in the card header
    Given the API returns a commuter entry for "Ryan" with mode "office"
    When the TravelCard for "Ryan" renders
    Then the card header contains "Ryan"

  Scenario: Two route alternatives are shown per card
    Given the API returns a commuter entry for "Ryan" with 2 route alternatives
    When the TravelCard for "Ryan" renders
    Then 2 route options are shown on the "Ryan" card

  Scenario: Route description is shown on each route option
    Given the API returns a route for "Ryan" with description "via A3 and M25"
    When the TravelCard for "Ryan" renders
    Then the text "via A3 and M25" is visible on the "Ryan" card

  Scenario: Travel time is displayed in minutes
    Given the API returns a route for "Ryan" with travel_time_seconds 2700
    When the TravelCard for "Ryan" renders
    Then "45 min" is visible on the "Ryan" card

  Scenario: Green colour state is rendered for a low-delay route
    Given the API returns a route for "Ryan" with delay_colour "green"
    When the TravelCard for "Ryan" renders
    Then the route card has a green colour indicator

  Scenario: Amber colour state is rendered for a moderate-delay route
    Given the API returns a route for "Ryan" with delay_colour "amber"
    When the TravelCard for "Ryan" renders
    Then the route card has an amber colour indicator

  Scenario: Red colour state is rendered for a high-delay route
    Given the API returns a route for "Ryan" with delay_colour "red"
    When the TravelCard for "Ryan" renders
    Then the route card has a red colour indicator

  # --- Incidents ---

  Scenario: Incidents are shown on the card when present
    Given the API returns a commuter entry for "Ryan" with 1 incident "Roadworks on A3"
    When the TravelCard for "Ryan" renders
    Then the incident "Roadworks on A3" is visible on the "Ryan" card

  Scenario: Incident section is not shown when no incidents
    Given the API returns a commuter entry for "Ryan" with 0 incidents
    When the TravelCard for "Ryan" renders
    Then no incident section is rendered on the "Ryan" card

  Scenario: Each card shows only its own commuter's incidents
    Given the API returns "Ryan" with 1 incident "Roadworks on A3"
    And "Emily" with 0 incidents
    When the dashboard renders
    Then the "Ryan" card shows the incident "Roadworks on A3"
    And the "Emily" card shows no incident section

  # --- Route label ---

  Scenario: Office route card shows destination as work
    Given the API returns a commuter entry for "Ryan" with mode "office" and no drops
    When the TravelCard for "Ryan" renders
    Then the route destination label is "Work"

  Scenario: Out-and-back route card shows destination as home
    Given the API returns a commuter entry for "Ryan" with mode "wfh" and drops ["dog"]
    When the TravelCard for "Ryan" renders
    Then the route destination label is "Home"

  # --- Stale state ---

  Scenario: Stale data indicator is shown when is_stale is true
    Given the API response has is_stale true
    When the dashboard renders
    Then a stale data warning is visible

  # --- Loading and error states ---

  Scenario: Loading state shown while data is fetching
    Given the API has not yet responded
    When the dashboard renders
    Then a loading indicator is visible

  Scenario: Error state shown when the API call fails
    Given the API returns an error
    When the dashboard renders
    Then an error message is visible
