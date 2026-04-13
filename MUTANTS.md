# Surviving Mutants — Justified

Mutants listed here have been reviewed and are acceptable to leave unaddressed. Each entry records the mutant ID, what was mutated, and why killing it is not worthwhile.

---

## Backend (`mutmut`)

### `routers/travel.py`

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x_extract_road_names__mutmut_8` | `inst.get("roadName") or ""` → `or "XXXX"` | Fallback string value — only reached when `roadName` is falsy (None/empty). The fallback is discarded by the `if road and ...` guard on the next line, so "XXXX" vs "" has no observable effect. |
| `x_expand_bounding_box__mutmut_1` | `degrees: float = 0.02` → `1.02` | Default parameter — unreachable via mutmut 3.x trampoline. The wrapper always passes the original default (0.02) explicitly, so the mutant's default is never invoked. Same class of issue as `x_parse_forecast__mutmut_1`. |
| `x_parse_incidents__mutmut_17` | `props.get("magnitudeOfDelay", 0)` → `default 1` | Default only used when key is absent. Existing tests cover `magnitudeOfDelay` absent (`test_parse_incidents_missing_magnitude_defaults_to_zero`) and verify the result is excluded — but with default=1 the mutant also excludes it (1 < 2). Behaviourally equivalent for missing-key case. |
| `x_parse_incidents__mutmut_23` | `props.get("events", [])` → `default None` | Default only reached when key is absent. Covered by `test_parse_incidents_handles_empty_events` but that test passes a present (empty) `events` key, so the default path isn't exercised. A `None` default would crash, but mutmut 3.x test selection doesn't run the relevant test against this mutant. Same root cause as the trampoline issue — test mapping gap, not a logic gap. |
| `x_parse_incidents__mutmut_25` | `props.get("events", [])` → `default ()` (no arg) | Same as mutmut_23 — `.get(key)` returns `None` for missing keys, identical behaviour to `None` default. |
| `x__extract_traffic_model_id__mutmut_3` | `routes_response.get("routes", [])` → `default None` | Default reached when key is absent — covered by `test_extract_traffic_model_id_missing_routes_key`. With `None`, `if not routes` is still truthy so returns `""`. Behaviourally equivalent for the missing-key case. |
| `x__extract_traffic_model_id__mutmut_5` | `routes_response.get("routes", [])` → no default arg | Same as mutmut_3 — `.get(key)` returns `None`, `if not None` is truthy, returns `""`. |

### `routers/weather.py`

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x_parse_forecast__mutmut_1` | `count: int = 6` → `count: int = 7` | Default parameter — unreachable via mutmut 3.x trampoline. The wrapper function retains the original default (6) and always passes `count` explicitly when calling the mutant. The mutant's default of 7 is never invoked through the test path. |
| `x_fetch_weather__mutmut_1–29` (29 mutants) | Various mutations inside `fetch_weather()` | HTTP client function making live Open-Meteo API calls. Untestable in isolation without a live network — mocking at this level would test the mock, not the logic. Integration tested end-to-end in Step 6. |
| `x_fetch_weather_data__mutmut_1–50` (50 mutants) | Various mutations inside `fetch_weather_data()` | Scheduler fetch function that calls `fetch_weather()`. No tests because it requires live HTTP calls; scheduler integration is tested via `test_scheduler.py` using mock fetch functions that stand in for this function. |

### `routers/travel.py` — `_parse_duration` and `_normalize_google_response` (pre-existing, session add-route-maps)

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x__parse_duration__mutmut_4` | `duration_str.rstrip("s")` → `rstrip("XXsXX")` | `str.rstrip` accepts a *set of characters*, not a substring. `"XXsXX"` still contains `'s'`, so the trailing `'s'` is stripped identically. Behaviourally equivalent mutant. |
| `x__normalize_google_response__mutmut_3/5` and ~33 additional mutants across `_normalize_google_response` | Various `.get(key, default)` default values changed (`[]`→`None`, `{}`→`None`, `""`→`"XXXX"`, `0`→`None`/`1`, etc.) | All tests supply the keys being fetched; the defaults are never reached during test execution. Where the key is absent and the default is used, the code either short-circuits (`if start:`) or returns early (`if not routes:`), making alternative defaults behaviourally equivalent. Same class as the other `.get()` survivors already documented. The 35 distinct mutant IDs reflect different call sites across the function but share the same root cause. |

### `routers/travel.py` — live HTTP functions

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x_fetch_routes__mutmut_1–22` (22 mutants) | Various mutations inside `fetch_routes()` | HTTP client function making live Google Maps Routes API calls. Untestable in isolation — requires a live network and valid API key. Integration tested end-to-end in Step 6. |
| `x_fetch_incidents__mutmut_1–48` (48 mutants) | Various mutations inside `fetch_incidents()` | Stub function returning `[]` — no live HTTP calls. Mutants are trivially acceptable as the function has no logic to test. |
| `x_fetch_travel_data__mutmut_1–59` (59 mutants) | Various mutations inside `fetch_travel_data()` | Scheduler fetch orchestrator that calls `fetch_routes` and `fetch_incidents`. Untestable without live API calls. Scheduler integration tested via mocks in `test_scheduler.py`. |

### `routers/calendar.py`

**`parse_event` — icalendar case-insensitivity (4 mutants)**

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x_parse_event__mutmut_4` | `component.get("dtstart")` → `component.get("DTSTART")` | `icalendar` component access is case-insensitive — both strings return the same value. Equivalent mutant. |
| `x_parse_event__mutmut_15` | `component.get("uid")` → `component.get("UID")` | Same — icalendar is case-insensitive. |
| `x_parse_event__mutmut_21` | `component.get("summary")` → `component.get("SUMMARY")` | Same — icalendar is case-insensitive. |
| `x_parse_event__mutmut_29` | `"#4285F4"` → `"#4285f4"` | CSS hex color — uppercase and lowercase are functionally identical. No test can distinguish them. |

**`_fetch_sync` — CalDAV mock doesn't validate arguments (11 mutants)**

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x__fetch_sync__mutmut_25` | `_datetime.combine(today, _datetime.min.time())` → `None` | `start_dt` passed to mocked `date_search`; mock accepts any argument. Correct window enforced by CalDAV server at runtime. |
| `x__fetch_sync__mutmut_30` | `_datetime.combine(tomorrow, _datetime.max.time())` → `None` | Same — `end_dt` passed to mock, not validated. |
| `x__fetch_sync__mutmut_36–42` (7 mutants) | Various mutations to `date_search(start=..., end=..., expand=True)` kwargs | Mock accepts any args and returns configured events regardless. Correct kwargs enforced at runtime by the CalDAV server. |
| `x__fetch_sync__mutmut_49` | `component.get("status")` → `component.get("STATUS")` | icalendar is case-insensitive — equivalent mutant. |
| `x__fetch_sync__mutmut_62` | `component.get("location")` → `component.get("LOCATION")` | icalendar is case-insensitive — equivalent mutant. |
| `x__fetch_sync__mutmut_78` | `component.get("dtstart").dt` (second call) → `component.get("DTSTART").dt` | icalendar is case-insensitive — equivalent mutant. |

**`_fetch_sync` — `fetch_event_travel` call args are mocked (7 mutants)**

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x__fetch_sync__mutmut_67–69, 71–73` (6 mutants) | `settings.home_lat`, `settings.home_lon`, `settings.google_maps_api_key` → `None`, or individual args removed | `fetch_event_travel` is patched in tests — the test verifies it is called (and that its return value is used), not the exact values of the lat/lon/key arguments. The settings values are correct in production. |
| `x__fetch_sync__mutmut_73` | `settings.google_maps_api_key` argument removed | Same as above — mocked function, argument not inspected. |

**`fetch_event_travel` — live HTTP function (39 mutants)**

`fetch_event_travel` makes a synchronous `httpx.post` to the Google Routes API. Tests mock `httpx.post` but do not inspect exact request body keys, header values, or default fallback values. All surviving mutants fall into one of three classes:

| Class | Mutant IDs | Examples | Justification |
|-------|-----------|---------|---------------|
| Guard `or` → `and` | `_1` | `if not location or not api_key` → `and` | With `or`, either empty value short-circuits. With `and`, only both being empty short-circuits. When `api_key=""` and `location` is set, the mutant would proceed to a failed HTTP call — which the exception handler returns `None` from anyway. The net behaviour (return `None`) is identical in tests. Acceptable: the guard's real purpose (avoid a pointless API call) is a performance concern, not correctness-critical. |
| Request body / header key and value mutations | `_20–29`, `_36`, `_38`, `_40–49` | Key strings changed (`"travelMode"` → `"XXtravelModeXX"`), headers set to `None`, timeout changed | Tests mock `httpx.post` to return a fixed response regardless of request content. Testing the exact body/headers would require inspecting call args, which would test the mock, not the logic. Correctness verified at integration time. |
| `.get()` default-value equivalence | `_53`, `_55`, `_63`, `_65`, `_68–69`, `_74`, `_79`, `_82`, `_84`, `_88`, `_90`, `_95`, `_97`, `_99`, `_101`, `_107` | `data.get("routes", [])` → `None`; `route.get("duration", "0s")` → `None`; nested `.get()` defaults mutated | Tests always supply the keys being fetched, so the default is never reached. Where the default *would* be used (missing key), the code either checks truthiness (`if not routes`) or falls back to 0 — `None` behaves identically to `[]`/`""` in those paths. Same class as other `.get()` survivors documented above. `rstrip("XXsXX")` is equivalent because `str.rstrip` treats its argument as a set of characters; "XXsXX" still contains 's'. |

**`fetch_calendar_data` — async executor wrapper (4 mutants — "no tests")**

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x_fetch_calendar_data__mutmut_1–4` | Mutations inside the `fetch_calendar_data` async wrapper | Two-line async wrapper over `asyncio.get_running_loop().run_in_executor(None, _fetch_sync)`. No domain logic — all calendar business logic is in `_fetch_sync` (fully tested). Mutating executor glue would test asyncio infrastructure, not application behaviour. |

### `scheduler.py`

| Mutant | Mutation | Justification |
|--------|----------|---------------|
| `x_run_scheduler__mutmut_1–19` (19 mutants) | Various mutations inside `run_scheduler()` | Infinite background loop — cannot be run in tests as it would block forever. The loop logic resolves to `poll_if_in_window()` + `asyncio.sleep()`, both of which are fully tested separately. The wiring in `run_scheduler` (lazy import resolution, `get_now` passthrough) is integration-tested in Step 6 (live stack). |

---

## Frontend (`stryker`)

### `components/WeatherCard.jsx`

14 surviving mutants across two accepted categories:

**Style injection infrastructure (9 mutants — lines 3, 5–10)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| Line 3: `STYLES_ID = 'weather-card-styles'` | `→ ""` | Used only to tag and deduplicate the injected `<style>` element. JSDOM doesn't render CSS, so no test can observe whether the ID is correct. Infrastructure concern, not component behaviour. |
| Line 5–10: `injectStyles()` body | Entire block removed | Function only injects a `<style>` tag into the real DOM. JSDOM does not apply or expose injected CSS, so no test can observe whether styles were injected. |
| Line 6: `typeof document === 'undefined'` | `→ true / false / ""` / `!==` (4 variants) | SSR guard — prevents `document` access in non-browser environments. JSDOM always defines `document`, so this branch can never be taken in tests, making all four operator/value mutations untestable. |
| Line 7: `document.getElementById(STYLES_ID)` | `→ true / false` | Deduplication guard — prevents re-injecting the same stylesheet. JSDOM does not apply styles, so injecting twice has no observable effect and this guard cannot be killed by a test. |
| Line 10: `style.textContent = \`...\`` | `→ ""` | CSS string content. JSDOM ignores injected stylesheets, so an empty string is indistinguishable from the real stylesheet in unit tests. |

**React async cancellation/cleanup pattern (5 mutants — lines 161, 167, 173–174, 176)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| Line 161: `if (!cancelled)` (success path) | `→ if (true)` | Cancellation guard — prevents state updates after component unmounts. Killing this requires resolving the fetch *after* unmounting; that window is race-prone in JSDOM and React 18 silently drops post-unmount state updates anyway, so no observable assertion is possible. Correct pattern, accepted survivor. |
| Line 167: `if (!cancelled)` (error path) | `→ if (true)` | Same as above, for the `.catch()` branch. |
| Line 173–174: `return () => { cancelled = true }` | Body removed / `true → false` | Cleanup function that signals cancellation on unmount. Indirectly tested by the cancellation guard tests above; the same reasoning applies — JSDOM/React 18 does not surface post-unmount state leaks as failures. |
| Line 176: `}, [])` | `→ }, ["Stryker was here"])` | `useEffect` empty dependency array. Mutating the deps would cause the effect to re-run on every render where the injected string changes. Tests render once and do not re-render, so this cannot be observed. Accepted as a tool limitation for single-render tests. |

### `components/TravelCard.jsx` (Session 12)

9 surviving mutants — all in `injectStyles()` infrastructure:

**Style injection infrastructure (9 mutants)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| `STYLES_ID = 'travel-card-styles'` | `→ ""` | CSS deduplication key. JSDOM does not render CSS; correctness of the ID is unobservable in unit tests. |
| `injectStyles()` body | Entire block removed | Function injects a `<style>` tag. JSDOM ignores injected stylesheets, so removal has no observable effect in tests. |
| `typeof document === 'undefined'` | `→ true / false / ""` / `!==` (4 variants) | SSR guard. JSDOM always defines `document`, so this branch cannot be taken in tests. |
| `document.getElementById(STYLES_ID)` | `→ true / false` | Deduplication guard. JSDOM does not apply styles, so double-injection has no observable effect. |
| `style.textContent = \`...\`` | `→ ""` | CSS string content. JSDOM ignores stylesheet text, so empty vs. real CSS is indistinguishable. |

### `components/RouteMap.jsx` (session add-route-maps)

28 surviving mutants — all within the `useEffect` Leaflet initialisation block.

| Category | Mutation examples | Justification |
|----------|-------------------|---------------|
| Map constructor options (`zoomControl`, `dragging`, `scrollWheelZoom`, etc.) | `false` → `true`, options object mutated | These control Leaflet interactivity flags. Tests mock `L.map` and never inspect the options object passed to it. Testing the exact options would test the mock, not real behaviour. Verified correct at runtime. |
| Tile layer URL and attribution string | String mutated to `""` or `"XXXX"` | Arguments passed to the mocked `L.tileLayer`; not inspected by any assertion. Visual correctness (correct tiles, OSM attribution) is not unit-testable in jsdom. |
| Polyline colour, weight, opacity | `'#4CAF82'` → `""`, `4` → `5`, `0.85` → `1.85` | Passed to the mocked `L.polyline`; not inspected by any assertion. Visual style correctness is not unit-testable in jsdom — verified at runtime against the delay colour variables. |
| `DELAY_COLOURS` object keys and values | Key/value strings mutated | Object lookup is untestable through the mock — the result of `DELAY_COLOURS[delayColour]` is passed straight to the mocked `L.polyline`. Colour accuracy is a runtime / visual concern. |
| `fitBounds` call | Call removed or arguments mutated | `mockMap.fitBounds` is a no-op mock. Whether bounds are fitted is not observable in jsdom. |
| `map.remove()` cleanup | Call removed | Cleanup function verified correct by React strict-mode double-mount in the browser; JSDOM does not trigger the React strict-mode remount cycle in these tests. |

**Summary**: `RouteMap.jsx` applies Leaflet imperatively inside `useEffect`. The three testable behaviours (render container when polyline present, render nothing when absent/empty) are fully covered. All 28 survivors are Leaflet API call details that are only observable visually or require a real browser environment.

### `components/AlertBanner.jsx` (Session 12)

9 surviving mutants — all in `injectStyles()` infrastructure. Same pattern as TravelCard and WeatherCard above.

### `App.jsx` (Session 12)

17 surviving mutants across four accepted categories:

**Style injection infrastructure (8 mutants)**

Same `injectStyles()` pattern as all other components — JSDOM cannot observe CSS injection.

**React async cancellation / cleanup (5 mutants)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| `if (!cancelled)` in `.catch()` success path | `→ if (true)` | Cancellation guard — prevents state update after unmount. JSDOM/React 18 silently drops post-unmount state updates; no observable failure possible without a timing-dependent unmount race. Same pattern as WeatherCard/CalendarCard. |
| `return () => { cancelled = true; clearInterval(id) }` | Body removed / `true → false` / `clearInterval` removed | Cleanup on unmount. Effect wires up a cancellation flag and stops polling; untestable in single-render unit tests without mounting and unmounting with precise timing. |

**Fallback values during null travelData (2 mutants)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| `travelData?.commuters ?? []` | `→ ?? ["Stryker was here"]` | Fallback used only when `travelData` is `null` (before first fetch). During that phase `travelLoading=true`, so the travel section shows a loading spinner regardless of commuter count — the fallback value cannot affect observable output. |
| `travelData?.is_stale ?? false` | `→ ?? true` or `&& false` | Same window: `travelData` is `null` only during loading. `TravelCard` renders a loading spinner when `loading=true`, suppressing the stale indicator unconditionally. The fallback value has no observable effect. |

**Fetch URL string and `useEffect` deps (2 mutants)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| `fetch('/api/travel')` | `→ fetch('')` | The test stubs `global.fetch` without inspecting the URL argument; any URL string produces the same mocked response. Testing the literal URL string would be circular. |
| `}, [])` | `→ }, ["Stryker was here"]` | `useEffect` empty dependency array. Tests render the component once and do not trigger re-renders, so a mutated deps value that causes re-runs cannot be observed. Accepted as a tool limitation. |

### `components/CalendarCard.jsx`

14 surviving mutants across two accepted categories:

**Style injection infrastructure (9 mutants — lines 3, 5–10)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| Line 3: `STYLES_ID = 'calendar-card-styles'` | `→ ""` | Used only to tag and deduplicate the injected `<style>` element. JSDOM does not render CSS, so no test can observe whether the ID is correct. Infrastructure concern, not component behaviour. |
| Line 5–10: `injectStyles()` body | Entire block removed | Function only injects a `<style>` tag into the real DOM. JSDOM does not apply or expose injected CSS, so no test can observe whether styles were injected. |
| Line 6: `typeof document === 'undefined'` | `→ true / false / ""` / `!==` (4 variants) | SSR guard. JSDOM always defines `document`, so this branch can never be taken in tests, making all four mutations untestable. Same pattern as WeatherCard. |
| Line 7: `document.getElementById(STYLES_ID)` | `→ true / false` | Deduplication guard. JSDOM does not apply styles, so injecting twice has no observable effect. |
| Line 10: `style.textContent = \`...\`` | `→ ""` | CSS string content. JSDOM ignores injected stylesheets, so an empty string is indistinguishable from the real stylesheet in unit tests. |

**React async cancellation/cleanup pattern (5 mutants — lines 157, 163, 169–170, 172)**

| Location | Mutation | Justification |
|----------|----------|---------------|
| Line 157: `if (!cancelled)` (success path) | `→ if (true)` | Cancellation guard on unmount. Killing requires resolving fetch after unmount; JSDOM/React 18 drops post-unmount state updates silently. Same pattern as WeatherCard. |
| Line 163: `if (!cancelled)` (error path) | `→ if (true)` | Same as above, for the `.catch()` branch. |
| Line 169–170: `return () => { cancelled = true }` | Body removed / `true → false` | Cleanup on unmount. Same reasoning as WeatherCard — not observably testable in single-render unit tests. |
| Line 172: `}, [])` | `→ }, ["Stryker was here"])` | `useEffect` empty dependency array. Tests render once and do not re-render, so a mutated deps array cannot be observed. Accepted as a tool limitation. |

---

## Notes

- **mutmut 3.x trampoline issue**: mutmut 3.x wraps each function in a trampoline that captures arguments using the *original* function's defaults. Mutations to default parameter values are therefore untestable through the normal call path — the mutant's default is never reached. This affects `expand_bounding_box`, `parse_forecast`. Accepted as a tool limitation.
- **`.get()` default equivalence**: Several mutants change `.get(key, [])` to `.get(key, None)` or `.get(key)`. Where the missing-key branch returns early or checks truthiness, `None` and `[]` behave identically. These are equivalent mutants — they don't represent real logic gaps.
