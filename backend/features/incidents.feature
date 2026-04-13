Feature: Traffic incident warnings per commuter via HERE Traffic API

  The dashboard shows traffic incidents affecting each commuter's route.
  Incidents are fetched from the HERE Traffic API using a bounding box
  derived from that commuter's route points only — not shared across commuters.
  Only moderate (criticality ≥ 2) and major incidents are shown.

  Background:
    Given the HERE Traffic API is available with a valid API key
    And the dashboard has at least one active commuter with a computed route

  Scenario: Moderate incident on a commuter's route is displayed
    Given a HERE incident with criticality 2 and type "ACCIDENT" on "M25"
    When incidents are fetched for that commuter's route bounding box
    Then the incident appears in that commuter's incident list
    And the incident has a road label of "M25" and a description

  Scenario: Major incident on a commuter's route is displayed
    Given a HERE incident with criticality 3 and type "ROAD_CLOSED" on "A3"
    When incidents are fetched for that commuter's route bounding box
    Then the incident appears in that commuter's incident list

  Scenario: Minor incident is excluded
    Given a HERE incident with criticality 1
    When incidents are fetched for a commuter's route bounding box
    Then the commuter's incident list is empty

  Scenario: Unknown-severity incident is excluded
    Given a HERE incident with criticality 0
    When incidents are fetched for a commuter's route bounding box
    Then the commuter's incident list is empty

  Scenario: HERE response with no incidents yields an empty list
    Given the HERE API returns an empty results array for a commuter's bounding box
    When incidents are fetched
    Then the commuter's incident list is empty

  Scenario: Incidents are fetched separately for each active commuter
    Given two active commuters with different routes
    When travel data is fetched
    Then the HERE API is called exactly once per active commuter
    And each commuter receives only the incidents from their own API call

  Scenario: Incident bounding box is derived from the commuter's route points
    Given an active commuter with a computed route
    When travel data is fetched
    Then fetch_incidents is called with a bounding box covering that commuter's route points

  Scenario: No HERE API key configured results in no incidents
    Given the HERE_API_KEY environment variable is not set
    When incidents are fetched for a commuter's route bounding box
    Then no HTTP request is made to HERE
    And the commuter's incident list is empty

  Scenario: HERE incident with missing description renders without a description
    Given a HERE incident with criticality 2 but no description field
    When incidents are fetched for a commuter's route bounding box
    Then the incident appears with an empty description

  Scenario: HERE incident with missing location renders without a road label
    Given a HERE incident with criticality 2 but no location field
    When incidents are fetched for a commuter's route bounding box
    Then the incident appears with an empty road label
