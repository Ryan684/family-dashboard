Feature: Dog walk route backend
  Background:
    Given the commute schedule is loaded
    And walk routes are configured in walk-routes.json
    And muddiness thresholds are set to defaults

  Scenario: Dog is at daycare today — endpoint returns not eligible
    Given today is a dog daycare day
    When the dashboard requests the dog-walk endpoint
    Then the response contains eligible: false
    And the response contains no routes

  Scenario: Dog is not at daycare today — endpoint returns eligible with routes
    Given today is not a dog daycare day
    And Open-Meteo returns dry conditions
    When the dashboard requests the dog-walk endpoint
    Then the response contains eligible: true
    And the response contains a ranked list of routes

  Scenario: Dry conditions — all routes are suitable
    Given today is not a dog daycare day
    And recent precipitation is below the muddy threshold
    And soil moisture is below the muddy threshold
    When the dashboard requests the dog-walk endpoint
    Then all routes have suitable: true
    And the conditions label is "Dry"

  Scenario: Wet conditions — high mud-sensitivity routes are marked unsuitable
    Given today is not a dog daycare day
    And recent precipitation exceeds the muddy threshold
    When the dashboard requests the dog-walk endpoint
    Then routes with mud_sensitivity 3 have suitable: false
    And routes with mud_sensitivity 1 have suitable: true
    And the conditions label is "Wet"

  Scenario: Very wet conditions — soil moisture also exceeds threshold
    Given today is not a dog daycare day
    And recent precipitation exceeds the muddy threshold
    And soil moisture exceeds the muddy threshold
    When the dashboard requests the dog-walk endpoint
    Then routes with mud_sensitivity 2 or higher have suitable: false
    And routes with mud_sensitivity 1 have suitable: true
    And the conditions label is "Very wet"

  Scenario: Routes are ranked with suitable routes first
    Given today is not a dog daycare day
    And wet conditions make some routes unsuitable
    When the dashboard requests the dog-walk endpoint
    Then suitable routes appear before unsuitable routes in the response

  Scenario: No routes configured — endpoint returns eligible with empty routes
    Given today is not a dog daycare day
    And walk-routes.json contains no routes
    When the dashboard requests the dog-walk endpoint
    Then the response contains eligible: true
    And the response contains an empty routes list

  Scenario: Open-Meteo data is unavailable — conditions default to unknown
    Given today is not a dog daycare day
    And Open-Meteo returns an error
    When the dashboard requests the dog-walk endpoint
    Then the response contains eligible: true
    And all routes have suitable: true
    And the conditions label is "Unknown"
