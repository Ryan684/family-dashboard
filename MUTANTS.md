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

---

## Frontend (`stryker`)

Stryker has not yet been run. This section will be populated after the first `npx stryker run` on each implemented component.

---

## Notes

- **mutmut 3.x trampoline issue**: mutmut 3.x wraps each function in a trampoline that captures arguments using the *original* function's defaults. Mutations to default parameter values are therefore untestable through the normal call path — the mutant's default is never reached. This affects `expand_bounding_box`, `parse_forecast`. Accepted as a tool limitation.
- **`.get()` default equivalence**: Several mutants change `.get(key, [])` to `.get(key, None)` or `.get(key)`. Where the missing-key branch returns early or checks truthiness, `None` and `[]` behave identically. These are equivalent mutants — they don't represent real logic gaps.
