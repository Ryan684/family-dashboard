Feature: Dynamic commutes backend — per-commuter schedule-driven routing

  Background:
    Given the routing API is available
    And a commute schedule config with two commuters "Ryan" and "Emily"
    And today is a weekday

  # --- Office routes ---

  Scenario: Office commuter with no drops gets a direct home-to-work route
    Given "Ryan" has mode "office" today with no drops
    When the travel endpoint is called
    Then the response contains a commuter entry for "Ryan"
    And "Ryan" has 2 route alternatives from home to work
    And "Ryan" mode is "office"
    And "Ryan" drops list is empty

  Scenario: Office commuter with nursery drop gets a waypoint route via nursery
    Given "Ryan" has mode "office" today
    And today is a nursery day
    And "Ryan" has nursery_drop true in their schedule
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home via nursery to work
    And "Ryan" drops list contains "nursery"

  Scenario: Office commuter with dog drop gets a waypoint route via dog daycare
    Given "Ryan" has mode "office" today with no nursery drop
    And today is a dog daycare day
    And "Ryan" is the weekly dog dropper
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home via dog daycare to work
    And "Ryan" drops list contains "dog"

  Scenario: Office commuter with both drops follows their configured drop order
    Given "Ryan" has mode "office" today
    And "Ryan" has drop_order ["dog", "nursery"]
    And today is a nursery day and a dog daycare day
    And "Ryan" has nursery_drop true and is the weekly dog dropper
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home via dog daycare then nursery to work
    And "Ryan" drops list is ["dog", "nursery"]

  Scenario: Drop order is respected per commuter
    Given "Emily" has mode "office" today
    And "Emily" has drop_order ["nursery", "dog"]
    And today is a nursery day and a dog daycare day
    And "Emily" has nursery_drop true and is the weekly dog dropper
    When the travel endpoint is called
    Then "Emily" has 2 route alternatives from home via nursery then dog daycare to work
    And "Emily" drops list is ["nursery", "dog"]

  # --- WFH routes ---

  Scenario: WFH commuter with no drops is omitted from the response
    Given "Ryan" has mode "wfh" today with no drops
    When the travel endpoint is called
    Then the response does not contain a commuter entry for "Ryan"

  Scenario: WFH commuter with dog drop gets an out-and-back route
    Given "Ryan" has mode "wfh" today
    And today is a dog daycare day
    And "Ryan" is the weekly dog dropper
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home via dog daycare back to home
    And "Ryan" drops list contains "dog"

  Scenario: WFH commuter with nursery drop gets an out-and-back route
    Given "Ryan" has mode "wfh" today
    And today is a nursery day
    And "Ryan" has nursery_drop true in their schedule
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home via nursery back to home
    And "Ryan" drops list contains "nursery"

  Scenario: WFH commuter with both drops gets a multi-waypoint out-and-back route
    Given "Ryan" has mode "wfh" today
    And "Ryan" has drop_order ["dog", "nursery"]
    And today is a nursery day and a dog daycare day
    And "Ryan" has nursery_drop true and is the weekly dog dropper
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home via dog daycare then nursery back to home

  # --- Day off routes ---

  Scenario: Day-off commuter with no drops is omitted from the response
    Given "Ryan" has mode "off" today with no drops
    When the travel endpoint is called
    Then the response does not contain a commuter entry for "Ryan"

  Scenario: Day-off commuter with drops gets an out-and-back route
    Given "Ryan" has mode "off" today
    And today is a dog daycare day
    And "Ryan" is the weekly dog dropper
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home via dog daycare back to home

  # --- Gate rules ---

  Scenario: Nursery gate blocks drop when today is not a nursery day
    Given "Ryan" has mode "office" today
    And "Ryan" has nursery_drop true in their schedule
    But today is not a nursery day
    When the travel endpoint is called
    Then "Ryan" has 2 route alternatives from home to work
    And "Ryan" drops list is empty

  Scenario: Dog gate blocks drop when today is not a dog daycare day
    Given "Ryan" has mode "office" today
    And "Ryan" is the weekly dog dropper
    But today is not a dog daycare day
    When the travel endpoint is called
    Then "Ryan" drops list is empty

  Scenario: Dog gate blocks drop when commuter is not the weekly dropper
    Given today is a dog daycare day
    And "Emily" is the weekly dog dropper
    And "Ryan" has mode "office" today
    When the travel endpoint is called
    Then "Ryan" drops list does not contain "dog"
    And "Emily" drops list contains "dog"

  # --- Multi-commuter response ---

  Scenario: Both active commuters appear in the response
    Given "Ryan" has mode "office" today with no drops
    And "Emily" has mode "office" today with no drops
    When the travel endpoint is called
    Then the response contains a commuter entry for "Ryan"
    And the response contains a commuter entry for "Emily"
    And the commuters array has 2 entries

  Scenario: Only active commuters appear when one is inactive
    Given "Ryan" has mode "office" today with no drops
    And "Emily" has mode "wfh" today with no drops
    When the travel endpoint is called
    Then the commuters array has 1 entry
    And the response contains a commuter entry for "Ryan"
    And the response does not contain a commuter entry for "Emily"

  Scenario: Commuters array is empty when both commuters are inactive
    Given "Ryan" has mode "wfh" today with no drops
    And "Emily" has mode "off" today with no drops
    When the travel endpoint is called
    Then the commuters array has 0 entries

  # --- Stale flag ---

  Scenario: Response is marked stale when outside poll window
    Given the current time is outside the configured poll window
    When the travel endpoint is called with a cached result
    Then the response field is_stale is true

  Scenario: Response is not stale when within poll window
    Given the current time is within the configured poll window
    When the travel endpoint is called
    Then the response field is_stale is false
