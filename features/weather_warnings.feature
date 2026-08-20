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

  The base URL, like the key, is issued at signup rather than a fixed or
  guessable value — the docs say plainly it "will have been supplied to you
  when you signed up and were given your API key." It is therefore config,
  optional for the same reason as the key: absent, the feature degrades to
  no warnings rather than the backend failing to start.

  Fetching warnings is a genuine two-step request, confirmed against the real
  Atom feed endpoint docs: first the Atom feed, to read the current "latest
  version of all issued warnings" URL from its feed-level related link, then
  that URL for the actual GeoJSON. The feed must be re-fetched on every poll
  rather than cached, because the URL it hands back rotates and a stale one
  404s.

  Background:
    Given the home location is configured with a latitude and longitude

  # --- Fetching ---

  Scenario: No API key means no request is made
    Given no Met Office API key is configured
    But a Met Office base URL is configured
    When warnings are fetched
    Then no HTTP request is made
    And an empty warning list is returned

  Scenario: No base URL means no request is made
    Given a Met Office API key is configured
    But no Met Office base URL is configured
    When warnings are fetched
    Then no HTTP request is made
    And an empty warning list is returned
  # The base URL is account-specific and cannot be hardcoded (see above), so
  # it is treated as exactly as required as the key — either missing is a
  # complete short circuit, not a partial one.

  Scenario: Fetching warnings is a two-step request
    Given a Met Office API key and base URL are configured
    When warnings are fetched
    Then exactly two HTTP requests are made
    And the first request is to the Atom feed endpoint
    And the second request is to the URL the feed's related link supplied

  Scenario: The second request uses the feed's own URL, not a composed one
    Given the Atom feed's related link points to a URL this app did not construct
    When warnings are fetched
    Then the second request is made to that exact URL
  # The related URL rotates on every feed update — composing it from a
  # pattern rather than reading it from the feed would eventually 404.

  Scenario: The API key is sent as a header on both requests
    Given a Met Office API key and base URL are configured
    When warnings are fetched
    Then both requests carry the key in an x-api-key header

  Scenario: An entry's own link is never mistaken for the feed's related link
    Given the Atom feed contains an entry with its own alternate link
    When warnings are fetched
    Then the second request still uses the feed-level related link
  # A per-entry rel="alternate" link describes one past change, not the
  # current full set of warnings — confirmed by the real Atom feed docs,
  # which describe the feed-level rel="related" link separately.

  Scenario: A feed with no related link yields no warnings
    Given the Atom feed has no related link
    When warnings are fetched
    Then no second HTTP request is made
    And an empty warning list is returned

  Scenario: A malformed feed yields no warnings
    Given the Atom feed response is not valid XML
    When warnings are fetched
    Then an empty warning list is returned

  # --- Parsing the feed ---

  Scenario: A warning's fields are extracted from a GeoJSON feature
    Given the feed returns one warning feature
    When the feed is parsed
    Then the warning has an id, level, weather type, headline and geometry

  Scenario: Weather type is a list of hazards, not a single value
    Given the feed returns a warning with weatherType ["WIND", "RAIN"]
    When the feed is parsed
    Then the warning's weather types are ["WIND", "RAIN"]
    # A warning can carry more than one hazard at once — confirmed by the real
    # API docs, where the example is itself a single-element list, ["THUNDERSTORM"].

  Scenario: A weatherType that is not a list is treated as absent
    Given the feed returns a warning with weatherType as a bare string
    When the feed is parsed
    Then the warning's weather types are empty
    # Guards against silently iterating a string character-by-character.

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
    Given the feed returns a warning with status "CANCELLED"
    When the feed is parsed
    Then no warnings are returned

  Scenario: An expired warning is discarded
    Given the feed returns a warning with status "EXPIRED"
    When the feed is parsed
    Then no warnings are returned

  Scenario: A warning with no status is kept
    Given the feed returns a warning with no status field
    When the feed is parsed
    Then one warning is returned
  # The real API's Issued endpoint already excludes CANCELLED and EXPIRED
  # warnings from its response — confirmed in the docs — so this filter is a
  # defensive backstop against a future schema change, not something the real
  # feed is expected to ever need in practice.

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
