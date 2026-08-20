Feature: Dashboard layout — travel section visibility
  The travel section is only shown during the poll window. Outside the
  window the is_stale flag is true and the section is removed from the
  layout entirely, and tomorrow's forecast takes the freed column so the
  grid keeps three content columns either way.

  The two are exact complements: whenever travel is shown tomorrow is not,
  and whenever travel is hidden tomorrow is. Stacking tomorrow beneath
  today instead was rejected — today's card runs to roughly 660px at three
  locations, past the column's height, so a stacked tomorrow would fall
  below the fade on exactly the days it matters.

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

  Scenario: Tomorrow section shown when the travel section is hidden
    Given the API returns commuters with is_stale true
    When the dashboard renders
    Then the tomorrow section is present in the layout

  Scenario: Tomorrow section hidden when the travel section is shown
    Given the API returns commuters with is_stale false
    When the dashboard renders
    Then the tomorrow section is not present in the layout

  Scenario: Tomorrow section shown when there are no commuters
    Given the API returns an empty commuters list with is_stale false
    When the dashboard renders
    Then the tomorrow section is present in the layout

  Scenario: Tomorrow section hidden while travel is still loading
    Given the travel API call has not yet resolved
    When the dashboard renders
    Then the tomorrow section is not present in the layout

  Scenario: Masthead heading is not rendered
    Given the dashboard renders
    Then no "Family Dashboard" heading text is shown
    And no "<Weekday> Edition" heading text is shown
