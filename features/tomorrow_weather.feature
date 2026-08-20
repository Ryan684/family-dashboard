Feature: Tomorrow's weather backend
  Outside the commute poll window the travel column is removed from the layout,
  freeing a third of the display. The weather endpoint fills it by also returning
  tomorrow's forecast, resolved against TOMORROW's commute schedule — so an office
  day tomorrow shows that office's weather, not today's.

  Open-Meteo returns both days from one request, so the coordinate sets for the two
  days are unioned and fetched once each. On the common day, where tomorrow's modes
  match today's, this costs no extra API calls at all.

  Tomorrow's entries carry no "current" block: a future day has no current
  conditions, and giving it one would invite a card that renders a fake "now"
  temperature.

  Background:
    Given the home location is configured with a latitude and longitude
    And two commuters are configured with their respective work locations

  # --- Resolving tomorrow's weekday ---

  Scenario: Tomorrow's weekday follows today's
    Given today is Monday
    When tomorrow's weekday is resolved
    Then the weekday is "tuesday"

  Scenario: Tomorrow's weekday wraps from Sunday to Monday
    Given today is Sunday
    When tomorrow's weekday is resolved
    Then the weekday is "monday"

  Scenario: Tomorrow's locations follow tomorrow's commute modes
    Given commuter "Ryan" has mode "office" tomorrow
    And commuter "Robyn" has mode "wfh" tomorrow
    When tomorrow's weather locations are resolved
    Then the locations are Ryan's office and Home

  Scenario: A weekend tomorrow resolves everyone to home
    Given tomorrow is Saturday and has no schedule entry
    When tomorrow's weather locations are resolved
    Then the response contains exactly one location entry named "Home"

  # --- Unioning the two days' fetch targets ---

  Scenario: Identical location sets produce no extra fetch targets
    Given today's and tomorrow's locations have the same coordinates
    When the fetch targets are resolved
    Then the number of fetch targets equals the number of today's locations

  Scenario: A location only needed tomorrow adds one fetch target
    Given today resolves to Home only
    And tomorrow resolves to Home and Ryan's office
    When the fetch targets are resolved
    Then two fetch targets are returned

  Scenario: A coordinate needing geocoding on either day is marked for geocoding
    Given a coordinate is an office tomorrow but home today
    When the fetch targets are resolved
    Then that fetch target is marked for geocoding

  # --- Parsing an arbitrary day ---

  Scenario: The daily high can be read for tomorrow
    Given Open-Meteo returns daily maximum temperatures of 18.1 and 21.4
    When the daily high is parsed for day index 1
    Then the daily high is 21.4

  Scenario: A daily high beyond the end of the data is None
    Given Open-Meteo returns a single daily maximum temperature
    When the daily high is parsed for day index 1
    Then the daily high is None

  Scenario: Daily rainfall can be read for tomorrow
    Given Open-Meteo returns precipitation sums of 0.0 and 3.1
    And precipitation probability maxima of 10 and 70
    When the rainfall is parsed for day index 1
    Then daily_rainfall contains total_mm 3.1 and probability_percent 70

  Scenario: Rainfall handles the two daily lists having different lengths
    Given Open-Meteo returns two precipitation sums but only one probability
    When the rainfall is parsed for day index 1
    Then total_mm is set and probability_percent is None

  Scenario: A daily weather description is derived for tomorrow
    Given Open-Meteo returns daily weather codes of 0 and 61
    When the daily description is parsed for day index 1
    Then the description is "Light rain"

  Scenario: A missing daily weather code list yields no description
    Given Open-Meteo returns a daily block with no weather codes
    When the daily description is parsed
    Then the description is None

  Scenario: An unrecognised daily weather code still yields a description
    Given Open-Meteo returns a daily weather code not in the known set
    When the daily description is parsed
    Then the description is "Unknown"

  # --- Rain windows for tomorrow ---

  Scenario: Tomorrow's rain windows are reported in tomorrow's own hours
    Given 48 hourly probabilities with rain at absolute hours 32 to 35
    When rain windows are parsed for day index 1
    Then one window is returned covering hours 8 to 12

  Scenario: Tomorrow's rain windows never run past the end of the day
    Given 48 hourly probabilities with rain from absolute hour 44 to the end
    When rain windows are parsed for day index 1
    Then the window ends at hour 24

  Scenario: Asking for tomorrow when only today was fetched returns no windows
    Given 24 hourly probabilities
    When rain windows are parsed for day index 1
    Then no windows are returned

  # --- Daylight saving ---

  Scenario: The clocks-back day has 25 hours and tomorrow still starts correctly
    Given hourly timestamps covering a 25-hour local day
    When the day offset is resolved for day index 1
    Then the offset is 25

  Scenario: The clocks-forward day has 23 hours and tomorrow still starts correctly
    Given hourly timestamps covering a 23-hour local day
    When the day offset is resolved for day index 1
    Then the offset is 23

  Scenario: A response without timestamps falls back to whole days
    Given hourly data with no time list
    When the day offset is resolved for day index 1
    Then the offset is 24

  # --- Weather glyphs ---

  Scenario: A clear sky code maps to the sun glyph
    Given a WMO weather code of 0
    When the glyph is derived
    Then the glyph is "sun"

  Scenario: A rain code maps to the rain glyph
    Given a WMO weather code of 61
    When the glyph is derived
    Then the glyph is "rain"

  Scenario: An overcast code maps to the cloud glyph
    Given a WMO weather code of 3
    When the glyph is derived
    Then the glyph is "cloud"

  Scenario: Today's locations carry a glyph derived from current conditions
    Given Open-Meteo returns a current weather code of 61 for home
    When the dashboard requests the weather endpoint
    Then the today location entry has icon "rain"

  # --- Endpoint payload ---

  Scenario: The endpoint returns tomorrow alongside today
    Given the weather cache holds today's and tomorrow's forecasts
    When the dashboard requests the weather endpoint
    Then the response contains a tomorrow block with a weekday and locations

  Scenario: Tomorrow's entries carry no current conditions
    Given the weather cache holds tomorrow's forecast
    When the dashboard requests the weather endpoint
    Then no tomorrow location entry contains a current block

  Scenario: An empty cache omits tomorrow entirely
    Given the weather cache is empty
    When the dashboard requests the weather endpoint
    Then the response contains no tomorrow block
    And the response contains an empty locations list
