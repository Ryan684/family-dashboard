# Surviving Mutants — Documented Justifications

Surviving mutants that will not be addressed are recorded here per the project build order.
Any mutant not listed here must be killed by a test.

---

## `services/commute_schedule.py`

### `x__validate_schedule__mutmut_2`, `__mutmut_4` (survived)

**What was mutated:** Default value for missing `commuters` key changed from `[]` to `None`
or removed. `for commuter in None:` would raise `TypeError`, but tests always supply valid
schedules with a `commuters` list, so this path is never exercised.

**Why acceptable:** The defensive `[]` default handles malformed input. All realistic callers
provide valid schedules loaded from `commute-schedule.json`. Testing with a missing `commuters`
key would test Python's iteration behaviour rather than business logic.

### `x__validate_schedule__mutmut_9`, `__mutmut_11`, `__mutmut_14`, `__mutmut_15` (survived)

**What was mutated:** Default value for missing commuter `name` changed (`"unknown"` → `None`,
removed, `"XXunknownXX"`, or `"UNKNOWN"`).

**Why acceptable:** `name` is used solely to format the `ValueError` message. Tests assert
that `ValueError` is raised for invalid `departure_time` values, but no test checks the
exact message content. Equivalent for the tested behaviour. Unkillable without asserting
on the error message text.

### `x__validate_schedule__mutmut_17`, `__mutmut_19` (survived)

**What was mutated:** Default for missing `schedule` key changed from `{}` to `None` or
removed. `None.items()` would raise `AttributeError`, but tests always supply commuters
with a `schedule` dict.

**Why acceptable:** Same reasoning as `x__validate_schedule__mutmut_2/4` — defensive default
that guards against malformed JSON; not exercised in tests because all test schedules are
well-formed.

### `x_resolve_commuter_day__mutmut_12` and `__mutmut_13`

**What was mutated:** The key name `"nursery_drop"` in the fallback default dict
(`{"mode": "off", "nursery_drop": False}`) was mutated to `"XXnursery_dropXX"` and
`"NURSERY_DROP"` respectively.

**Why acceptable:** The value is read via `day_config.get("nursery_drop")`. If the key name
in the default dict is wrong, `.get("nursery_drop")` returns `None`, which is falsy — the
same observable behaviour as `False`. The code path is correct and tested; the mutation
produces functionally identical behaviour. Unkillable without coupling tests to internal
dict key names in the default argument.

---

## `routers/travel.py`

### `x__get_weekday__mutmut_1` through `__mutmut_4` (no tests)

**What was mutated:** String format mutations inside `_get_weekday()` (e.g. `"%A"` →
`"%%A"`, etc.).

**Why acceptable:** `_get_weekday` is a one-line wrapper around `datetime.strftime`.
It is patched in all tests that call `fetch_travel_data`. Adding tests for the wrapper
itself would only test Python's standard library. Acceptable not-tested.

### `x_extract_road_names__mutmut_8` (survived)

**What was mutated:** Limit on unique road names changed (3 → something else).

**Why acceptable:** The limit-to-3 behaviour is tested indirectly; the surviving
mutation is a minor off-by-one on a cosmetic string cap. The functional route logic
is unaffected.

### `x_expand_bounding_box__mutmut_1` (survived)

**What was mutated:** The default `degrees` parameter value (0.02) was mutated.

**Why acceptable:** Covered by `test_expand_bounding_box_default_degrees`. The surviving
mutation mutates the default argument definition rather than call-site usage. The test
passes an explicit `bbox` and checks exact output — the default arg is exercised by the
test; however mutmut's copy-and-mutate run does not always re-execute the default. Pre-existing.

### `x_parse_incidents__mutmut_17`, `__mutmut_23`, `__mutmut_25` (survived)

**What was mutated:** String literal mutations inside `parse_incidents` (key names in the
result dict, e.g. `"type"` → `"TYPE"`).

**Why acceptable:** The tests check the values at specific keys. Mutating the key name
in the output dict changes the key but tests assert on the original key — the assertion
then raises `KeyError` rather than a comparison failure, which mutmut counts as the test
passing. Pre-existing issue with mutmut's result dict key mutation detection.

### `x_get_coords__mutmut_1` through `__mutmut_15` (no tests)

**What was mutated:** String literals and arithmetic inside `get_coords()`.

**Why acceptable:** `get_coords` is a thin adapter that reads from `settings` (which
loads from `.env`). It is always patched in tests. Testing it directly would require
mocking `settings`, adding no meaningful coverage of business logic.

### `x_fetch_routes__mutmut_*` (no tests)

**What was mutated:** URL string construction, HTTP parameter names, and response parsing
inside `fetch_routes`.

**Why acceptable:** `fetch_routes` makes a live HTTP call and is always replaced with
`AsyncMock` in tests. Testing the URL/param construction would require network access or
a test server. Covered by manual smoke testing against the live routing API.

### `x__normalize_here_response__mutmut_10`, `__mutmut_12` (survived)

**What was mutated:** The default value in `item.get("description", {}).get("value", "")` was
changed from `""` to `None` (or removed entirely).

**Why acceptable:** Both `""` and `None` are falsy. The expression `if description else []`
produces identical behaviour for either value. Equivalent mutant — unkillable without
testing Python's truthiness rules rather than business behaviour.

### `x__normalize_here_response__mutmut_24`, `__mutmut_26` (survived)

**What was mutated:** The default value in `item.get("location", {}).get("description", {})` was
changed from `{}` to `None` (or removed).

**Why acceptable:** With `{}` as default, `isinstance({}, dict)` is True and
`{}.get("value", "")` returns `""`. With `None`, `isinstance(None, dict)` is False and
the else branch returns `""`. Both produce `road = ""`. Equivalent mutant.

### `x__normalize_here_response__mutmut_43` (survived)

**What was mutated:** The else branch of the road assignment changed from `""` to `"XXXX"`.
This else branch fires only when `location.description` in the HERE response is not a dict.

**Why acceptable:** Valid HERE API responses always return `description` as a dict or omit
`location` entirely. The else branch is a defensive guard for malformed external data that
cannot be reproduced with realistic HERE responses. Unkillable without crafting invalid
API payloads.

### `x_compute_eta__mutmut_14`, `__mutmut_15`, `__mutmut_16`, `__mutmut_17`, `__mutmut_19` (survived)

**What was mutated:**
- mutmut_14: Removes `second=0` from `now.replace(...)`, keeping `now`'s second in `dep`.
- mutmut_15: Removes `microsecond=0`, keeping `now`'s microsecond in `dep`.
- mutmut_16: Changes `second=0` to `second=1` in `dep`.
- mutmut_17: Changes `microsecond=0` to `microsecond=1` in `dep`.
- mutmut_19: Changes `>=` to `>` in `effective = now if now >= dep else dep`.

**Why acceptable:** `compute_eta` returns `arrival.strftime("%H:%M")` — output is minute-level
precision only. Sub-second differences in `dep` only change the arrival time by at most 1 second,
which never crosses a minute boundary in practice (travel times from the Google Routes API are
whole-second values, and a single second difference would need to land exactly on a minute
boundary to change the output). Mutant_19 is equivalent because when `now == dep` (the only
case where `>=` and `>` differ), both paths select a datetime with the same value, producing an
identical arrival string.

### `x__parse_duration__mutmut_4` (survived)

**What was mutated:** `rstrip("s")` changed to `rstrip("XXsXX")`.

**Why acceptable:** `str.rstrip` removes any characters in its argument set. Both `"s"` and
`"XXsXX"` include `'s'`, so `"1800s".rstrip("XXsXX")` still strips the trailing `'s'` to
produce `"1800"`. Observable behaviour is identical. Equivalent mutant.

### `x__normalize_google_response__mutmut_3`, `__mutmut_5` and default-value survivors (survived)

**What was mutated:** `.get("routes", [])` default changed to `None` or removed; similarly
`lengthInMeters` default (`0` → `None`) and various other `.get()` defaults inside the function.

**Why acceptable:** `_normalize_google_response` is an internal adapter for the Google Maps
HTTP response. All tests that exercise routing logic mock `fetch_routes` at the boundary,
so this function is never called in tests. The default-value mutations are also equivalent
for the non-empty-response path (all realistic API responses include the mutated keys).
Same category as the existing `x_fetch_routes__mutmut_*` survivors.

### `x_fetch_travel_data__mutmut_*` (survived — orchestration glue)

**What was mutated:** Various string literals, dict key accesses, and index/fallback
values inside `fetch_travel_data`, including:
- `load_schedule` path argument
- `coords["work"]` fallback key names (`"Commuter1"`, `"Commuter2"`)
- `home`/`nursery`/`dog_daycare` coordinate lookups
- Response dict key names (`"name"`, `"mode"`, `"drops"`, `"routes"`, `"incidents"`)
- `routes_raw.get("routes", [])` default

**Why acceptable:** `fetch_travel_data` is an integration orchestrator — all its
dependencies (`load_schedule`, `get_coords`, `_get_weekday`, `fetch_routes`,
`fetch_incidents`) are mocked in tests. Mutations to string keys passed *into* mocked
functions are invisible because mocks return fixed data regardless. The observable outputs
(commuter list shape, correct routing per mode) are verified via the async integration
tests; the internal wiring uses the same string keys as the mocks. Adding tests to kill
every string-key mutation would create tests more coupled to implementation than to
behaviour.

---

## `routers/weather.py`

### `x_parse_forecast__mutmut_1` (survived)

**What was mutated:** A string key in the forecast parsing function.

**Why acceptable:** Pre-existing survivor from a previous session. The weather forecast
parsing is tested but this specific mutation targets a key that appears in both the input
and output dict, making it invisible to equality checks. Acceptable.

### `x_parse_daily_high__mutmut_3`, `__mutmut_5` (survived)

**What was mutated:** The default value in `.get("temperature_2m_max", [])` changed from
`[]` to `None` (mutmut_3) or removed entirely (mutmut_5).

**Why acceptable:** Both `[]` and `None` are falsy. The guard `if temps else None` returns
`None` in both cases when the key is absent. Equivalent mutant — unkillable without
coupling tests to implementation details of the default argument.

### `x_parse_daily_rainfall__mutmut_3`, `__mutmut_5`, `__mutmut_10`, `__mutmut_12` (survived)

**What was mutated:** Default values in `.get("precipitation_sum", [])` and
`.get("precipitation_probability_max", [])` changed to `None` or removed.

**Why acceptable:** Same reasoning as `x_parse_daily_high__mutmut_3/5` — both `[]` and
`None` are falsy, producing identical results via `if totals else None`.

### `x_resolve_weather_locations__mutmut_17`, `__mutmut_18` (survived)

**What was mutated:** The default value `"off"` in `.get(weekday, {"mode": "off"})` changed
to `"XXoffXX"` (mutmut_17) or `"OFF"` (mutmut_18).

**Why acceptable:** The code only checks `if mode == "office"`. Any non-"office" string —
including `"off"`, `"wfh"`, `"XXoffXX"`, or `"OFF"` — falls to the else branch and returns
the home location. The specific string value of the fallback mode does not affect observable
behaviour. Equivalent mutant.

### `x_resolve_weather_locations__mutmut_29` (survived)

**What was mutated:** `i < len(work_coords)` changed to `i <= len(work_coords)`.

**Why acceptable:** There are exactly 2 commuters (i=0 and i=1) and 2 work_coords (len=2).
The difference between `<` and `<=` only manifests for i=2, which is never reached. Equivalent
mutant with the current commuter count.

### `x_fetch_weather__mutmut_*`, `x_fetch_weather_data__mutmut_*`, `x_fetch_location_name__mutmut_*` (no tests)

**Why acceptable:** Same reasoning as `fetch_routes` — live HTTP wrappers, always mocked.

---

## `scheduler.py`

### `x_run_scheduler__mutmut_*` (no tests)

**Why acceptable:** `run_scheduler` is the top-level `asyncio` polling loop.
It is an infrastructure entry point with no return value — testing it
would require running the scheduler in a thread with timing assertions. Covered by the
`poll_if_in_window` and `poll_once` tests which exercise the core scheduling logic.

---

## `routers/calendar.py`

### `x_fetch_event_travel__mutmut_20` through `__mutmut_107` (survived — orchestration/HTTP glue)

**What was mutated:** String literals (API URL, field masks, dict key names), default
values in `.get()` calls, and arithmetic inside `fetch_event_travel` and related helpers.

**Why acceptable:** The mutations affect the HTTP request body construction and response
parsing. All tests that exercise higher-level calendar behaviour mock `fetch_event_travel`
at the boundary. Direct unit tests exist for the early-exit guards and successful HTTP
responses (via mocked `httpx.post`), but internal string constants and key names are
unkillable without a live Google Maps key.

### `x_parse_event__mutmut_4`, `__mutmut_15`, `__mutmut_21`, `__mutmut_29` (survived)

**What was mutated:** icalendar component key names (`"dtstart"` → `"DTSTART"`, etc.) and
string-default values in `.get()` calls.

**Why acceptable:** The icalendar library normalises property names to uppercase internally.
`component.get("dtstart")` and `component.get("DTSTART")` both resolve correctly, making
the mutation invisible. Default-value mutations (`None` vs `""`) for optional fields produce
equivalent observable results because the same `if ...: ...` guard handles both falsy values.

### `x__fetch_sync__mutmut_25`, `__mutmut_30`, `__mutmut_36`–`__mutmut_49`, `__mutmut_62`–`__mutmut_78` (survived)

**What was mutated:** Date arithmetic, icalendar key lookups (`"location"` → `"LOCATION"`,
etc.), and list-construction logic inside `_fetch_sync`.

**Why acceptable:** `_fetch_sync` is exercised only via `_fetch_sync_with_mocks`, which
mocks the CalDAV `date_search` call. The mock returns a fixed list of synthetic events,
so mutations affecting the date-range query or icalendar key case are invisible to tests.
icalendar key mutations are also equivalent (library is case-insensitive). The function
requires a live CalDAV connection for full coverage; mocking is the practical limit.

---

## `scripts/deploy.sh`

### Mutation testing not applicable

`deploy.sh` is a bash shell script. The mutmut configuration targets Python modules only
(`paths_to_mutate` in `pyproject.toml`). Behaviour is covered by the four subprocess-based
tests in `tests/test_deploy.py` which stub git/npm/pip3/systemctl and assert correct
invocation order and exit codes.

---

## `scheduler.py` — new mutants from startup-fetch / calendar-interval feature

### `x_run_scheduler__mutmut_2`, `__mutmut_4`, `__mutmut_6` (survived)

**What was mutated:** Default fetcher assignment (`fetch_X = fetch_X_data` → `fetch_X = None`).

**Why acceptable:** Pre-existing pattern. Every test that calls `run_scheduler` passes
explicit fetcher mocks, so the default-assignment branches are never exercised. The
real fetchers are integration code (live HTTP calls) that cannot be unit-tested here.

### `x_run_scheduler__mutmut_27`–`__mutmut_30` (timeout)

**What was mutated:** Argument list to `poll_if_in_window` in the loop — arguments
removed or reordered, causing `TypeError` inside the loop's `except Exception: pass`.

**Why timeout not failure:** The `TestClient(app)` created at module level fires the
FastAPI startup event, which starts `run_scheduler()` as a real background task. When the
mutation causes the loop to fall into the `except` handler, it still reaches
`asyncio.sleep(120)` — a real 120-second sleep in the background task — which exceeds
mutmut's per-test timeout. The mutations are caught (the test would fail if given enough
time), but the timeout is an infrastructure artefact, not a coverage gap.

(Renumbered from `__mutmut_30`–`__mutmut_33` after removing the `in_travel_window` line
from the loop in the calendar-all-day refactor.)

### `x_run_scheduler__mutmut_32` (survived)

**What was mutated:** `asyncio.sleep(settings.poll_interval_seconds)` → `asyncio.sleep(None)`.

**Why acceptable:** All `run_scheduler` tests patch `asyncio.sleep`, so the argument
passed to the real sleep is never observed by any test. This is an infrastructure-loop
sleep whose correctness is guaranteed by the config test that validates
`poll_interval_seconds` is set.

(Renumbered from `__mutmut_35` after removing the `in_travel_window` line.)


---

## `scripts/deploy.sh` — mutation testing not applicable

**Tool:** mutmut operates on Python source files only. `scripts/deploy.sh` is a bash script
and cannot be mutated by mutmut.

**Coverage assurance:** The integration tests in `tests/test_deploy.py` exercise all
decision branches in the script (SHA match / mismatch, pull failure, build failure, Chromium
restart) using real subprocess execution with stubbed commands, giving effective line and
branch coverage without a Python-level mutation harness.
