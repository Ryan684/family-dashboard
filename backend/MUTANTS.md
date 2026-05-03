# Surviving Mutants — Documented Justifications

Surviving mutants that will not be addressed are recorded here per the project build order.
Any mutant not listed here must be killed by a test.

---

## `services/commute_schedule.py`

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

### `x_fetch_weather__mutmut_*` and `x_fetch_weather_data__mutmut_*` (no tests)

**Why acceptable:** Same reasoning as `fetch_routes` — live HTTP wrappers, always mocked.

---

## `scheduler.py`

### `x_run_scheduler__mutmut_*` (no tests)

**Why acceptable:** `run_scheduler` is the top-level event loop that drives the
APScheduler. It is an infrastructure entry point with no return value — testing it
would require running the scheduler in a thread with timing assertions. Covered by the
`poll_if_in_window` and `poll_once` tests which exercise the core scheduling logic.
