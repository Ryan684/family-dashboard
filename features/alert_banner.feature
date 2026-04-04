Feature: Morning alert banner

  The alert banner appears at the top of the dashboard when any commute route
  has a significant delay (red threshold: > 25% above no-traffic time).
  Dismissed state is not required for v1.

  Background:
    Given the dashboard receives travel data from the API

  Scenario: Banner shown when a home-to-work route is red
    Given a home-to-work route has delay_colour "red"
    When the alert banner is rendered
    Then the alert banner is visible
    And it displays a message advising the user to leave earlier

  Scenario: Banner shown when a home-to-nursery route is red
    Given a home-to-nursery route has delay_colour "red"
    When the alert banner is rendered
    Then the alert banner is visible
    And it displays a message advising the user to leave earlier

  Scenario: Banner not shown when all routes are green or amber
    Given all routes have delay_colour of "green" or "amber"
    When the alert banner is rendered
    Then the alert banner is not visible

  Scenario: Banner not shown when travel data is null
    Given travel data has not yet loaded
    When the alert banner is rendered
    Then the alert banner is not visible

  Scenario: Banner shown when the worst route across both destinations is red
    Given a home-to-work route has delay_colour "green"
    And a home-to-nursery route has delay_colour "red"
    When the alert banner is rendered
    Then the alert banner is visible
