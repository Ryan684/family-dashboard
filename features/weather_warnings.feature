Feature: Met Office severe weather warnings backend
  Open-Meteo has no alerts endpoint, so severe weather warnings come from the Met
  Office National Severe Weather Warning Service (NSWWS) instead.

  The API key is obtained by application rather than self-serve, so the whole
  feature is optional: with no key configured the fetch short-circuits, the
  endpoint returns an empty list and the banner never appears. Nothing errors and
  nothing needs redeploying when the key is eventually added to .env — the key is
  read as an ordinary optional setting, never a required one, because config is
  evaluated at import time and a missing required value would take the backend
  down at the next nightly deploy.

  Warnings ride on the weather poll rather than a fourth scheduler source: the
  120-second weather cadence already matches the Met Office's own guidance of
  polling every one to two minutes, and they are served from the same cache.

  Background:
    Given the home location is configured with a latitude and longitude

  # --- Fetching ---

  Scenario: No API key means no request is made
    Given no Met Office API key is configured
    When warnings are fetched
    Then no HTTP request is made
    And an empty warning list is returned

  Scenario: The API key is sent as a header
    Given a Met Office API key is configured
    When warnings are fetched
    Then the request carries the key in an x-api-key header

  # --- Parsing the feed ---

  Scenario: A warning's fields are extracted from a GeoJSON feature
    Given the feed returns one warning feature
    When the feed is parsed
    Then the warning has an id, level, weather type, headline and geometry

  Scenario: An empty feature collection parses to no warnings
    Given the feed returns no features
    When the feed is parsed
    Then no warnings are returned

  Scenario: A feature with no properties is skipped
    Given the feed returns a feature with no properties block
    When the feed is parsed
    Then no warnings are returned

  Scenario: Warning levels are upper-cased so comparisons are stable
    Given the feed returns a warning with level "amber"
    When the feed is parsed
    Then the warning level is "AMBER"

  Scenario: A cancelled warning is discarded
    Given the feed returns a warning with status "Cancelled"
    When the feed is parsed
    Then no warnings are returned

  Scenario: An expired warning is discarded
    Given the feed returns a warning with status "Expired"
    When the feed is parsed
    Then no warnings are returned

  Scenario: A warning with no status is kept
    Given the feed returns a warning with no status field
    When the feed is parsed
    Then one warning is returned

  # --- Matching warnings to our locations ---

  Scenario: A warning covering home is kept and names it
    Given a warning whose area covers the home coordinates
    When the warning is matched against our locations
    Then the warning is kept
    And its locations list is ["Home"]

  Scenario: A warning covering nowhere near us is discarded
    Given a warning whose area covers neither home nor any office
    When the warning is matched against our locations
    Then no warnings are returned

  Scenario: A warning covering several of our locations appears once
    Given a warning whose area covers both home and Ryan's office
    When the warning is matched against our locations
    Then exactly one warning is returned
    And its locations list is ["Home", "Guildford"]

  Scenario: A duplicated location name is only listed once
    Given the same location appears in both today's and tomorrow's lists
    And a warning covering it
    When the warning is matched against our locations
    Then its locations list contains that name once

  Scenario: Feed order is preserved for warnings of the same level
    Given two amber warnings both covering home
    When the warnings are matched against our locations
    Then both are returned in feed order

  # --- Ordering ---

  Scenario: Red warnings sort before amber
    Given an amber warning and a red warning
    When the warnings are sorted
    Then the red warning is first

  Scenario: Amber warnings sort before yellow
    Given a yellow warning and an amber warning
    When the warnings are sorted
    Then the amber warning is first

  Scenario: A tie in level is broken by higher impact
    Given two amber warnings with different warningImpact values
    When the warnings are sorted
    Then the higher-impact warning is first

  Scenario: A tie in level and impact is broken by higher likelihood
    Given two amber warnings with the same warningImpact but different warningLikelihood
    When the warnings are sorted
    Then the higher-likelihood warning is first

  Scenario: Level always outranks impact
    Given an amber warning with a higher warningImpact than a red warning
    When the warnings are sorted
    Then the red warning is still first

  Scenario: A warning with no impact rating sorts as least severe among ties
    Given two amber warnings, one with no warningImpact value
    When the warnings are sorted
    Then the warning with a warningImpact value is first
  # This ordering — level, then impact, then likelihood — matches the priority
  # Met Office's own docs describe for ranking warnings. The field names
  # (warningImpact, warningLikelihood, and everything else this feature and
  # weather_warning_banner.feature depend on) are confirmed against a real
  # captured NSWWS response, not assumed — see services/nswws.py's module
  # docstring for how and what remains unconfirmed.

  # --- Endpoint ---

  Scenario: Warnings are served from the weather cache
    Given the weather cache holds one warning
    When the dashboard requests the warnings endpoint
    Then the response contains that warning

  Scenario: An empty cache returns an empty warning list
    Given the weather cache is empty
    When the dashboard requests the warnings endpoint
    Then the response contains an empty warning list

  Scenario: A cache predating this feature returns an empty warning list
    Given the weather cache holds locations but no warnings key
    When the dashboard requests the warnings endpoint
    Then the response contains an empty warning list

  Scenario: Yellow warnings are returned by the API
    Given the weather cache holds a yellow warning
    When the dashboard requests the warnings endpoint
    Then the yellow warning is present in the response

  # Yellow is filtered in the frontend, not here — the API stays truthful about
  # what the Met Office issued, and the decision to hide it lives in one
  # predicate in the banner. See weather_warning_banner.feature.
