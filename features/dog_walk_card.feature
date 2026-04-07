Feature: Dog walk card frontend
  Background:
    Given the /api/dog-walk endpoint is available

  Scenario: Card is not rendered on a dog daycare day
    Given the API returns eligible: false
    When the App renders
    Then the DogWalkCard is not present in the DOM

  Scenario: Card is rendered on a non-daycare day
    Given the API returns eligible: true with at least one route
    When the DogWalkCard renders
    Then the card is visible

  Scenario: Loading state is shown while the API has not responded
    Given the API call has not yet resolved
    When the DogWalkCard renders
    Then a loading indicator is visible

  Scenario: Error state is shown when the API call fails
    Given the API call fails with a network error
    When the DogWalkCard renders
    Then an error message is visible

  Scenario: Top recommended route is displayed prominently
    Given the API returns eligible: true with a top route named "Park Loop"
    When the DogWalkCard renders
    Then "Park Loop" is displayed as the recommended route

  Scenario: Route duration and distance are displayed
    Given the API returns a route with duration 25 minutes and distance 2.1 km
    When the DogWalkCard renders
    Then "25 min" is displayed
    And "2.1 km" is displayed

  Scenario: Conditions label is displayed
    Given the API returns conditions label "Wet"
    When the DogWalkCard renders
    Then "Wet" is displayed as the conditions

  Scenario: Unsuitable routes are visually distinguished
    Given the API returns a route with suitable: false
    When the DogWalkCard renders
    Then that route is rendered with an unsuitable indicator

  Scenario: All routes are listed below the top recommendation
    Given the API returns eligible: true with 3 routes
    When the DogWalkCard renders
    Then 3 routes are visible in the card
