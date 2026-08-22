Feature: Tomorrow forecast card frontend
  The TomorrowCard occupies the column freed when the travel section is hidden,
  showing tomorrow's forecast beside today's so the two read as a comparison.

  It renders through the exact same shared location-block component as the
  weather card — same 88px headline figure, same fonts, same spacing — fed
  tomorrow's forecast data instead of today's. Tomorrow's payload carries no
  "current" reading (a future day has no live conditions), so the component's
  one visible difference is data-driven rather than a separate design: the
  headline figure falls back to the day's high, and the "High: X°C" sub-line
  is omitted since it would just repeat the headline number. Everything else
  — the glyph, the rain figure, the rain-window caption — is identical code
  to today's card, not a lookalike.

  It carries no column label at all — no card on the dashboard does. The
  content already identifies the column at a glance, so a text label was pure
  redundancy. Removing it, consistently across every card, is also what
  reclaims the vertical room that keeps a second weather location's detail
  visible when the traffic and weather alert straps are both up.

  Background:
    Given the /api/weather endpoint is available

  Scenario: Loading state is shown while the API has not responded
    Given the API call has not yet resolved
    When the TomorrowCard renders
    Then a loading indicator is visible

  Scenario: No "Tomorrow" column label is shown
    Given the API returns a tomorrow block with weekday "Wednesday"
    When the TomorrowCard renders
    Then no "Tomorrow" section label is visible
    And no weekday name is shown anywhere

  Scenario: Location name is displayed
    Given the API returns a tomorrow location named "Home"
    When the TomorrowCard renders
    Then "Home" is visible on screen

  Scenario: The daily high is displayed as the headline figure
    Given the API returns a tomorrow location with daily high 17°C
    When the TomorrowCard renders
    Then "17°C" is displayed

  Scenario: No separate "High:" line duplicates the headline figure
    Given the API returns a tomorrow location with daily high 17°C
    When the TomorrowCard renders
    Then no "High:" text is visible on screen
  # The shared component shows a separate "High:" line only when a location
  # also carries a live current reading distinct from it (today's card).
  # Tomorrow's headline figure IS the high, so a second line repeating the
  # same number would be pure duplication.

  Scenario: Weather description is displayed
    Given the API returns a tomorrow location with description "Light rain"
    When the TomorrowCard renders
    Then the weather description "Light rain" is displayed

  Scenario: Only tomorrow's own data is rendered, never today's
    Given the API returns today's locations with current temperature 8°C
    And a tomorrow location with daily high 17°C
    When the TomorrowCard renders
    Then "8°C" is not visible on screen
  # Confirms TomorrowCard reads only the payload's tomorrow.locations, never
  # today's locations — the two arrays share a response but must never mix.

  Scenario: Daily rainfall is displayed
    Given the API returns a tomorrow location with daily_rainfall total_mm 3.1 and probability_percent 70
    When the TomorrowCard renders
    Then "Rain: 3.1 mm · 70% chance" is displayed

  Scenario: Rainfall row is hidden when total_mm is zero
    Given the API returns a tomorrow location with daily_rainfall total_mm 0
    When the TomorrowCard renders
    Then no rainfall line is visible

  Scenario: Rainfall row is hidden when daily_rainfall is absent
    Given the API returns a tomorrow location without a daily_rainfall field
    When the TomorrowCard renders
    Then no rainfall line is visible

  Scenario: Rain windows are displayed when present
    Given the API returns a tomorrow location with rain_windows covering hours 14–17
    When the TomorrowCard renders
    Then "2–5pm" is displayed

  Scenario: Rain window row is hidden when rain_windows is empty
    Given the API returns a tomorrow location with an empty rain_windows array
    When the TomorrowCard renders
    Then no rain window row is visible

  Scenario: One block is rendered per tomorrow location
    Given the API returns two tomorrow locations
    When the TomorrowCard renders
    Then two tomorrow location blocks are visible

  Scenario: A payload without a tomorrow block shows an unavailable message
    Given the API response has no tomorrow key
    When the TomorrowCard renders
    Then a "Tomorrow unavailable" status is visible

  Scenario: An empty tomorrow locations list shows an unavailable message
    Given the API returns a tomorrow block with no locations
    When the TomorrowCard renders
    Then a "Tomorrow unavailable" status is visible

  Scenario: Error state is shown when the API call fails
    Given the API call fails with a network error
    When the TomorrowCard renders
    Then an error message is visible

  Scenario: Error state is shown when the API returns a non-ok status
    Given the API returns HTTP 500
    When the TomorrowCard renders
    Then an error message is visible

  Scenario: No stale indicator is shown, even when the data is cached
    Given the API response has is_stale true
    When the TomorrowCard renders
    Then no stale data warning is visible

  # The weather card, which always renders beside this one and reads the same
  # endpoint, already carries the indicator; a second one is duplication and
  # would also break the shared baseline the two columns need to read as a
  # comparison — an extra tag on one column but not the other pushes its first
  # location block down relative to its neighbour.
