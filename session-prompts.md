# Family Dashboard — Claude Code Session Prompts

Use these prompts at the start of each Claude Code session. Each session has a single scope and a hard stop condition. Do not combine sessions.

Reference: see `family-dashboard.md` for the full project specification.

---

## Session 1 — Project Scaffold

```
@family-dashboard.md

Scaffold the project structure from the spec. Do not implement any features or business logic.

Tasks:
1. Create the full folder structure from the Project Structure section
2. Initialise the FastAPI backend with a single GET /health endpoint returning {"status": "ok"}
3. Initialise the Vite + React frontend with a placeholder App.jsx that renders "Family Dashboard"
4. Create pyproject.toml with ruff and pytest config
5. Create package.json with Vitest, React Testing Library, ESLint, and Prettier configured
6. Create .claude/settings.json with the hooks from the spec
7. Create CLAUDE.md from the spec
8. Create .env.example from the spec
9. Create .gitignore covering .env, __pycache__, .venv, node_modules, .last-test-results, .claude-failures.jsonl
10. Confirm uvicorn starts the backend and npm run dev starts the frontend without errors

Stop after these tasks. Do not begin any feature work.
```

---

## Session 2 — ClockCard

```
@family-dashboard.md

Implement the ClockCard feature only. Follow the build order from the spec exactly.

Step 1: Write features/clock.feature
Step 2: Write frontend/src/components/ClockCard.test.jsx — tests must fail before implementation
Step 3: Read /mnt/wslg/distro/home/ryank/.claude/plugins/marketplaces/anthropic-agent-skills/skills/frontend-design/SKILL.md, then implement ClockCard.jsx applying the screen size design notes from the spec (24" landscape, 1-2m viewing distance, 48px+ primary text, dark theme, no hover states)
Step 4: Confirm all ClockCard tests pass
Step 5: Commit on a feature branch with a conventional commit message

Do not touch any other component or backend file. Stop after the commit.
```

---

## Session 3 — Travel Backend

```
@family-dashboard.md

Implement the travel backend route only. Do not touch the frontend.

Step 1: Write features/travel.feature covering: two routes returned, route description format, delay colour logic thresholds, and incident warnings
Step 2: Write backend/tests/test_travel.py — mock all TomTom API calls, tests must fail before implementation
Step 3: Implement backend/routers/travel.py — calculateRoute with maxAlternatives=1, route description extracted from guidance road names, bounding box derived from polyline for incident query, poll window enforcement from config
Step 4: Run pytest — all tests must pass
Step 5: Run mutmut — address any surviving mutants
Step 6: Commit on a feature branch

Do not implement the frontend TravelCard. Do not make live API calls during testing. Stop after the commit.
```

---

## Session 4 — TravelCard Frontend

```
@family-dashboard.md

Implement the TravelCard frontend component only. The backend /api/travel endpoint already exists.

Step 1: Write features/travel_card.feature covering the frontend behaviour — two route options displayed, description shown, colour state (green/amber/red) rendered correctly, incident list shown only when incidents present
Step 2: Write frontend/src/components/TravelCard.test.jsx — mock the API response, tests must fail before implementation
Step 3: Read /mnt/wslg/distro/home/ryank/.claude/plugins/marketplaces/anthropic-agent-skills/skills/frontend-design/SKILL.md, then implement TravelCard.jsx applying the screen size design notes from the spec
Step 4: Run vitest — all tests must pass
Step 5: Run Stryker — address surviving mutants
Step 6: Commit on a feature branch

Do not modify the backend. Do not implement any other component. Stop after the commit.
```

---

## Session 5 — Weather Backend

```
@family-dashboard.md

Implement the weather backend route only. Do not touch the frontend.

Step 1: Write features/weather.feature
Step 2: Write backend/tests/test_weather.py — mock all Open-Meteo calls, tests must fail before implementation
Step 3: Implement backend/routers/weather.py using Open-Meteo — current conditions and short forecast for the home location
Step 4: Run pytest — all tests must pass
Step 5: Run mutmut — address surviving mutants
Step 6: Commit on a feature branch

Stop after the commit.
```

---

## Session 6 — WeatherCard Frontend

```
@family-dashboard.md

Implement the WeatherCard frontend component only. The backend /api/weather endpoint already exists.

Step 1: Write features/weather_card.feature
Step 2: Write frontend/src/components/WeatherCard.test.jsx — mock the API response, tests must fail before implementation
Step 3: Read /mnt/wslg/distro/home/ryank/.claude/plugins/marketplaces/anthropic-agent-skills/skills/frontend-design/SKILL.md, then implement WeatherCard.jsx applying the screen size design notes from the spec
Step 4: Run vitest — all tests must pass
Step 5: Run Stryker — address surviving mutants
Step 6: Commit on a feature branch

Stop after the commit.
```

---

## Session 7 — Calendar Backend

```
@family-dashboard.md

Implement the Google Calendar backend route only. Do not touch the frontend.

Step 1: Write features/calendar.feature
Step 2: Write backend/tests/test_calendar.py — mock the Google Calendar API, tests must fail before implementation
Step 3: Implement backend/routers/calendar.py using google-api-python-client — fetch today and tomorrow's events from the configured shared calendar, OAuth credentials loaded from .env
Step 4: Run pytest — all tests must pass
Step 5: Run mutmut — address surviving mutants
Step 6: Commit on a feature branch

Stop after the commit.
```

---

## Session 8 — CalendarCard Frontend

```
@family-dashboard.md

Implement the CalendarCard frontend component only. The backend /api/calendar endpoint already exists.

Step 1: Write features/calendar_card.feature
Step 2: Write frontend/src/components/CalendarCard.test.jsx — mock the API response, tests must fail before implementation
Step 3: Read /mnt/wslg/distro/home/ryank/.claude/plugins/marketplaces/anthropic-agent-skills/skills/frontend-design/SKILL.md, then implement CalendarCard.jsx applying the screen size design notes from the spec. Events should be colour-coded per calendar. Today and tomorrow shown separately.
Step 4: Run vitest — all tests must pass
Step 5: Run Stryker — address surviving mutants
Step 6: Commit on a feature branch

Stop after the commit.
```

---

## Session 9 — AlertBanner + Layout Integration

```
@family-dashboard.md

Two tasks: implement AlertBanner, then wire all components into the final App.jsx layout.

Part 1 — AlertBanner:
Step 1: Write features/alert_banner.feature
Step 2: Write AlertBanner.test.jsx — tests must fail before implementation
Step 3: Implement AlertBanner.jsx — renders only when a route delay exceeds the red threshold, dismissed state not required for v1
Step 4: Run vitest — all tests pass

Part 2 — Layout:
Step 5: Update App.jsx to compose ClockCard, TravelCard, WeatherCard, CalendarCard, and AlertBanner into the final dashboard layout. Apply the 2-3 column grid from the screen size design notes. ClockCard spans full width at top.
Step 6: Read /mnt/wslg/distro/home/ryank/.claude/plugins/marketplaces/anthropic-agent-skills/skills/frontend-design/SKILL.md and review the overall layout for visual coherence — typography scale, spacing, dark theme consistency
Step 7: Run the full test suite (pytest + vitest) — all pass
Step 8: Commit on a feature branch

Stop after the commit.
```

---

## Session 10 — Scheduler and Polling

```
@family-dashboard.md

Wire up the background polling scheduler. Do not touch the frontend.

Step 1: Implement scheduler.py — polls travel, weather, and calendar routes on POLL_INTERVAL_SECONDS, respects POLL_WINDOW_START and POLL_WINDOW_END, caches results in memory
Step 2: Update main.py to start the scheduler on FastAPI startup and serve cached results from all /api/* routes
Step 3: Write tests covering: poll window enforcement (no calls outside window), cache is served when fresh, stale indicator flag set outside poll window
Step 4: Run pytest — all tests pass
Step 5: Run mutmut — address surviving mutants
Step 6: Confirm the full stack runs end-to-end on localhost with live data
Step 7: Commit on a feature branch

Stop after the commit.
```

---

## Model selection

**Default: Sonnet** for all sessions. It handles 90%+ of this project without compromise and is included in your Pro plan without extra cost.

**Opus** requires enabling extra usage on a Pro plan. Reserve it for Sessions 3 and 10 where architectural judgement is highest (travel backend coordination logic, scheduler cache design). Use `opusplan` mode — type `/plan` to enter plan mode with Opus thinking through the design, then Sonnet handles implementation automatically:

```
/model opusplan   # enable at session start
/plan             # triggers Opus for the planning phase only
```

Switch mid-session if you hit a genuinely tricky design decision:
```
/model opus    # switch to Opus temporarily
/model sonnet  # switch back for implementation
```

| Session | Recommended model | Reason |
|---|---|---|
| 1 — Scaffold | Sonnet | Mechanical setup, no design decisions |
| 2 — ClockCard | Sonnet | Simple frontend component |
| 3 — Travel backend | Sonnet + Opus /plan if needed | Complex coordination logic (bounding box, Traffic Model ID, poll window) |
| 4 — TravelCard | Sonnet | Frontend implementation |
| 5 — Weather backend | Sonnet | Straightforward API integration |
| 6 — WeatherCard | Sonnet | Frontend implementation |
| 7 — Calendar backend | Sonnet | Straightforward API integration |
| 8 — CalendarCard | Sonnet | Frontend implementation |
| 9 — AlertBanner + layout | Sonnet | Component composition |
| 10 — Scheduler | Sonnet + Opus /plan if needed | Cache design, poll window enforcement, startup coordination |

---

## General guidance

- Always paste the prompt exactly — do not paraphrase or summarise
- If a session goes off track, use `/clear` and restart with the same prompt rather than trying to course-correct
- Use `/compact` if a session runs long before continuing
- Between sessions run `git log --oneline` to confirm the branch and commit landed cleanly
- Write the feature file yourself before the session if you have 10 minutes — it makes the session tighter and cheaper