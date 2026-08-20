Feature: Severe weather warning banner
  A strap across the top of the dashboard when the Met Office has a severe weather
  warning covering one of this household's locations. It sits above the morning
  traffic alert: a red weather warning outranks a traffic delay, and the weather is
  usually what caused the traffic.

  Only amber and red reach the banner. UK yellow warnings fire several times a week
  in winter, often for routine rain and wind; a permanently lit strap is one nobody
  reads, and it would train the household to ignore the same strap when it carries a
  red warning. The backend still returns yellow — the decision to hide it lives in
  one predicate here.

  Unlike the traffic alert, this banner renders even when the data is cached. A
  stale travel delay is actively misleading because traffic has moved on; a stale
  weather warning is not, because Met Office warnings run for hours or days.

  Background:
    Given the /api/weather/warnings endpoint is available

  Scenario: Nothing is rendered when there are no warnings
    Given the API returns an empty warnings list
    When the WarningBanner renders
    Then nothing is rendered

  Scenario: Nothing is rendered while the API has not responded
    Given the API call has not yet resolved
    When the WarningBanner renders
    Then nothing is rendered

  Scenario: Nothing is rendered when the API call fails
    Given the API call fails with a network error
    When the WarningBanner renders
    Then nothing is rendered

  Scenario: Nothing is rendered when the API returns a non-ok status
    Given the API returns HTTP 500
    When the WarningBanner renders
    Then nothing is rendered

  # A kiosk strap reading "couldn't load warnings" is worse than silence.

  Scenario: An amber warning shows its headline
    Given the API returns one amber warning headlined "Heavy rain may cause flooding"
    When the WarningBanner renders
    Then "Heavy rain may cause flooding" is visible on screen

  Scenario: An amber warning is announced as a status
    Given the API returns one amber warning
    When the WarningBanner renders
    Then the banner has the status role

  Scenario: A red warning is announced as an alert
    Given the API returns one red warning
    When the WarningBanner renders
    Then the banner has the alert role

  Scenario: The severity is named in the banner
    Given the API returns one amber warning
    When the WarningBanner renders
    Then "Amber" is visible on screen

  Scenario: The affected locations are named
    Given the API returns a warning covering "Home" and "Guildford"
    When the WarningBanner renders
    Then "Home & Guildford" is visible on screen

  Scenario: A single affected location is named without a conjunction
    Given the API returns a warning covering only "Home"
    When the WarningBanner renders
    Then "Home" is visible on screen

  Scenario: A yellow warning does not raise the banner
    Given the API returns only a yellow warning
    When the WarningBanner renders
    Then nothing is rendered

  Scenario: A yellow warning alongside an amber one is not counted
    Given the API returns one yellow warning and one amber warning
    When the WarningBanner renders
    Then the amber warning is shown
    And no additional warning count is visible

  Scenario: The most severe warning governs the banner
    Given the API returns an amber warning followed by a red warning
    When the WarningBanner renders
    Then the red warning's headline is shown

  Scenario: Additional warnings are summarised as a count
    Given the API returns three amber warnings
    When the WarningBanner renders
    Then the first warning's headline is shown
    And "+2 more" is visible on screen

  Scenario: A single warning shows no count
    Given the API returns one amber warning
    When the WarningBanner renders
    Then no additional warning count is visible

  Scenario: The banner renders even when the data is cached
    Given the API returns one amber warning
    And the weather data is stale
    When the WarningBanner renders
    Then the warning is still visible

  Scenario: Both straps active — accepted trade-off, not a bug
    Given a red travel route makes the traffic alert visible
    And an amber-or-worse weather warning makes this banner visible
    When the dashboard renders
    Then both straps are shown, weather warning above traffic alert
    And the weather column's second location may lose its description, high
      temperature and rain windows under the bottom fade, because the two
      straps together leave less vertical room for the content columns
    # Confirmed by rendering the dashboard at 1920x1080: nothing overflows or
    # breaks visually, the second location's detail is simply not visible.
    # This combination requires a red route (only possible while travel is
    # shown) and a live amber-or-worse warning at the same time, so it is
    # confined to the 06:30-09:30 commute window. Accepted rather than adding
    # conditional banner padding with no scenario of its own to justify it.
