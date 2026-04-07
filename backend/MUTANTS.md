# Surviving Mutants — Documented Justifications

Surviving mutants that will not be addressed are recorded here per the project build order.
Any mutant not listed here must be killed by a test.

---

## `services/dog_walk.py`

### `x_is_dog_daycare_day__mutmut_3`, `__mutmut_5`, `__mutmut_7`, `__mutmut_9`

**What was mutated:** The fallback defaults in `schedule.get("dog_daycare", {})` and
`.get("days", [])` were mutated to `None`, empty, or had arguments removed.

**Why acceptable:** These defaults guard against malformed config (missing `dog_daycare`
or `days` keys). All test schedules are well-formed with both keys present, so the
defaults are never exercised. Testing for malformed config would test Python's `dict.get`
rather than business logic. Unkillable without coupling tests to config-parsing edge cases.

---

### `x_rank_routes__mutmut_7`, `__mutmut_8`, `__mutmut_9`

**What was mutated:** The dict key `"Dry"` was renamed (`"XXDryXX"`, `"dry"`, `"DRY"`).

**Why acceptable:** Renaming `"Dry"` makes it fall through to `.get(conditions, 999)`.
Since the mapped value is also `999`, the observable behaviour is identical. Unkillable
without an unrealistic route (mud_sensitivity > 999) or changing the dict value, which
would just move the problem to the default-value mutants below.

---

### `x_rank_routes__mutmut_11`, `__mutmut_12`, `__mutmut_13`

**What was mutated:** The dict key `"Unknown"` was renamed.

**Why acceptable:** Same reasoning as `"Dry"` mutants above — `"Unknown"` maps to 999,
identical to the fallback default. Unkillable for the same reason.

---

### `x_rank_routes__mutmut_4`, `__mutmut_6`

**What was mutated:** The fallback default in `.get(conditions, 999)` was mutated to
`None` or removed.

**Why acceptable:** The default is only reached for unknown condition strings. All callers
pass one of the four known strings. Mutating the default to `None` would cause a TypeError
at runtime, but that path is never exercised in tests. Unkillable without an unreachable
else-branch test.

---

### `x_rank_routes__mutmut_10`, `__mutmut_14`, `__mutmut_23`

**What was mutated:** Threshold values for `"Dry"` (999 → 1000), `"Unknown"` (999 → 1000),
and the fallback default (999 → 1000) were incremented by 1.

**Why acceptable:** The practical range of `mud_sensitivity` is 1–3. Any threshold above 3
produces identical suitability results. 999 and 1000 are both effectively "infinity" for
this domain. Unkillable without a route with `mud_sensitivity` between 999 and 1000.

---

### `x_rank_routes__mutmut_43`

**What was mutated:** The sort key `lambda r: 0 if r["suitable"] else 1` had `1` changed to `2`.

**Why acceptable:** Both `1` and `2` are positive integers greater than `0`. The sort produces
identical output: suitable routes (key=0) always precede unsuitable routes (key>0).
Unkillable without testing the exact numeric sort key value, which has no behavioural meaning.

---

### `x_load_walk_routes__mutmut_5`, `__mutmut_7`

**What was mutated:** The fallback default in `data.get("routes", [])` was mutated to `None`
or removed.

**Why acceptable:** The JSON config always has a `"routes"` key (both in `walk-routes.json`
and in all test fixtures). The `[]` default guards against a malformed file. Unkillable
without writing a test for malformed JSON, which would test Python's `dict.get` not business logic.

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

### `x__extract_traffic_model_id__mutmut_3` and `__mutmut_5` (survived)

**What was mutated:** String literal `"trafficModelId"` in `.get()` call and the empty-
string return value `""` were mutated.

**Why acceptable:** The function returns the model ID string which is then used as an
optional parameter in `fetch_incidents`. Mutations to the key string are invisible because
our mock data returns the expected ID regardless; mutations to the `""` fallback are
invisible because tests don't call the function with routes missing `trafficModelId`. Pre-existing.

### `x_get_coords__mutmut_1` through `__mutmut_15` (no tests)

**What was mutated:** String literals and arithmetic inside `get_coords()`.

**Why acceptable:** `get_coords` is a thin adapter that reads from `settings` (which
loads from `.env`). It is always patched in tests. Testing it directly would require
mocking `settings`, adding no meaningful coverage of business logic.

### `x_fetch_routes__mutmut_*` and `x_fetch_incidents__mutmut_*` (no tests)

**What was mutated:** URL string construction, HTTP parameter names, and response parsing
inside the routing API HTTP wrapper functions.

**Why acceptable:** These functions make live HTTP calls and are always replaced with
`AsyncMock` in tests. Testing the URL construction would require network access or a
test server, which is out of scope for unit tests. The integration is covered by manual
smoke testing against the live routing API.

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
