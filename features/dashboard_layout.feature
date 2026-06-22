Feature: Dashboard layout — travel section visibility
  The travel section is only shown during the poll window. Outside the
  window the is_stale flag is true and the section is removed from the
  layout entirely so the weather and calendar columns fill the available
  space, matching the weekend layout when no commuters are active.

  Scenario: Travel section hidden when data is stale
    Given the API returns commuters with is_stale true
    When the dashboard renders
    Then the travel section is not present in the layout

  Scenario: Travel section shown when data is fresh and commuters are active
    Given the API returns commuters with is_stale false
    When the dashboard renders
    Then the travel section is present in the layout

  Scenario: Travel section hidden when no commuters regardless of stale flag
    Given the API returns an empty commuters list with is_stale false
    When the dashboard renders
    Then the travel section is not present in the layout
