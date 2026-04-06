# Family Morning Dashboard — Project Documentation

## Overview

A wall-mounted family dashboard designed to ease the morning routine. Displays live travel ETAs for commute routes, weather at relevant locations, and upcoming calendar events from a shared family calendar — all visible at a glance before leaving the house.

---

## Hardware Options

### Recommended — Raspberry Pi 5 + 21–24" Touchscreen Monitor

The Pi 5 outputs 4K HDMI and will drive any monitor. At this screen size, mainstream touchscreen monitors are a better choice than Pi-specific displays — better panels, better value, and more mounting flexibility. Touch input runs over USB (HDMI for video, USB for touch), and works driver-free on Raspberry Pi OS with any modern touchscreen monitor.

| Component | Source | ~Cost |
|---|---|---|
| Raspberry Pi 5 (4GB) | The Pi Hut / Pimoroni | £55 |
| 21–24" touchscreen monitor (see suggestions below) | Amazon | £230–320 |
| Pi VESA mount bracket | Amazon / The Pi Hut / 3D print | £10–15 |
| Freestanding VESA monitor arm | Amazon | £30–50 |
| MicroSD card (32GB+) | Any | £8 |
| Official Pi 5 power supply | The Pi Hut | £12 |
| **Total** | | **~£345–460** |

**Monitor suggestions (21–24", all 1080p IPS, VESA 100x100, USB touch):**

| Model | Size | Approx. price | Notes |
|---|---|---|---|
| ViewSonic TD2465 | 24" | ~£300 | Consistently recommended in Pi community; 10-point touch |
| Hannspree HT249PPB | 24" | ~£250 | Well documented with Pi; solid IPS panel |
| AOC T2470W | 24" | ~£240 | Widely available; good value |

Final monitor choice TBD — confirm VESA 100x100 and USB touch before purchasing.

### Fallback — Android Tablet (Lenovo Tab M10 Plus)

- ~£150–180, no Pi required
- Uses Fully Kiosk Browser (~£7) to lock to dashboard URL on boot
- Battery management required for permanent wall mounting
- More setup friction; less control over the OS

### Not Recommended

- **Amazon Fire HD** — locked-down OS, sideloading friction
- **iPad** — expensive for a dedicated display; kiosk mode requires workarounds
- **Pi-specific displays under 15"** — too small for multi-card dashboard readability at kitchen distance

---

## Chosen Hardware Path

**Raspberry Pi 5 (4GB) + 21–24" mainstream touchscreen monitor**, to be purchased once the software is stable and tested on localhost.

---

## Physical Setup

### Pi mounting

The Pi mounts on the back of the monitor using a **VESA bracket**, making the whole unit self-contained with short internal cables. Options:

- **Ready-made bracket** — search "Raspberry Pi 5 VESA mount" on Amazon or The Pi Hut; fits 75x75mm or 100x100mm VESA patterns; ~£10–15
- **3D printed bracket** — well-rated designs on Printables.com if you have printer access; free to print, perfect fit for the Pi 5 case

With the Pi VESA-mounted behind the monitor, the only external cables are one power cable to the monitor and one to the Pi.

### Temporary freestanding setup (pre-move)

Rather than wall mounting before settling into the new house, use a **freestanding VESA monitor arm** with a weighted base sitting on a kitchen counter or sideboard:

- Holds the monitor at the right height and angle with no drilling
- The Pi is hidden on the back — looks like a single unit
- Fully portable — moves to the new house in minutes
- When ready to wall mount permanently, swap the freestanding arm for a wall bracket using the same VESA holes on the monitor

Look for a single-arm freestanding VESA stand supporting up to 27" and 10kg, with a 100x100mm VESA plate — widely available on Amazon for £30–50 (e.g. VIVO, Perlegear, WALI).

### Cable management

With the freestanding arm, run both power cables (monitor + Pi) down the back of the arm pole and bundle with velcro ties. A single cable run from the base to a nearby socket keeps the setup tidy without any wall work.

---

## Features

- **Clock & date** — large, always-visible time and date display; the most prominent element on the screen, legible from across the room at a glance
- **Travel ETAs** — per-commuter, schedule-driven routing. Each active commuter gets a card showing 2 fastest route alternatives with travel time, a brief route description (e.g. "via M25 and A3"), and colour-coded delay status (green / amber / red). Routes are multi-waypoint where applicable (e.g. home → dog daycare → nursery → work). Commuters who are WFH or off with no drops are hidden; the grid reflows. Traffic incident warnings for any incidents on or near a commuter's route are shown beneath their card.
- **Weather** — current conditions and short forecast for home and commute destination locations
- **Calendar** — upcoming events from shared family Google Calendar (today + tomorrow)
- **Morning alert banner** — contextual message if a route has significant delay (e.g. "Leave 15 mins early")

---

## Tech Stack

### Backend

- **Language:** Python 3.14
- **Framework:** FastAPI
- **Runtime:** Uvicorn
- **Scheduler:** APScheduler (or asyncio background tasks) — polls APIs on a configurable interval and caches results in memory, so the frontend just hits fast local endpoints
- **Environment config:** `python-dotenv` for API keys
- **Project config:** `pyproject.toml` for project metadata, dependencies, and tool configuration

### Frontend

- **React** (Vite) — component-per-card structure maps naturally to the dashboard layout (travel, weather, calendar, alert banner)
- Polls local FastAPI endpoints on a configurable refresh interval (e.g. every 60 seconds)
- Built with `npm run build` and served as static files by FastAPI in production — no separate Node process on the Pi
- Fullscreen in Chromium kiosk mode
- During development: Vite dev server proxies API requests to the local FastAPI backend

### Design Approach

Use the **Anthropic frontend-design skill** when building the UI (invoke via `/frontend-design`). Key principles:

- Commit to a bold, specific aesthetic direction — e.g. refined dark theme with strong typographic hierarchy and generous spacing
- Distinctive font pairing (avoid Inter/Roboto/system fonts)
- Subtle purposeful motion — e.g. a gentle pulse on an ETA card when a route is delayed
- CSS variables for a cohesive colour system
- Calm and readable at a glance — this is the primary constraint given the use case
- The `ClockCard` is the hero element — time should be the largest text on screen, date slightly smaller beneath it. No border or card chrome needed; it should feel like it belongs to the layout, not sit inside a box

#### Screen size design notes (21–24", landscape 1920×1080, viewed from ~1–2m)

Pass these notes to the frontend-design skill as context when building any UI component:

- **Pixel density vs. viewing distance** — at 1–2m from a 24" 1080p display, fine detail (hairline borders, small icons, subtle gradients) will be lost. Design for boldness, not intricacy
- **Generous whitespace** — cards should breathe; a layout that looks fine on a laptop will feel cramped at a glance from across a room. Prefer fewer, larger elements over many small ones
- **Minimum font sizes** — secondary text no smaller than 24px; primary information (ETA times, temperature, clock) should be 48px or larger
- **Card grid** — with 1920×1080 and 4–5 cards, a 2- or 3-column grid works well in landscape. ClockCard should span full width or sit prominently at the top; never squeezed into a corner
- **Touch targets** — any interactive element should be at least 48×48px and usable from a standing position without precision
- **No hover-dependent UI** — nothing important should be hidden behind hover states or tooltips; this is a wall-mounted touchscreen
- **Dark theme preferred** — high-contrast dark background outperforms light themes at distance and in variable kitchen lighting; target minimum 7:1 contrast ratio for primary text

### APIs

| Purpose | Provider | Notes |
|---|---|---|
| Travel — routes & ETAs | Google Maps Routes API (`computeRoutes`) | POST request with `computeAlternativeRoutes: true` returns 2 fastest routes. Each route includes travel time, static (no-traffic) duration, distance, and step-by-step navigation — road names extracted from step instructions to form a brief route description. Free tier: $200/month credit (well within personal dashboard usage). |
| Travel — incident warnings | N/A | Google Maps Routes API does not provide a direct traffic incident endpoint. Incidents are always returned as an empty array. The frontend incident display remains in place for potential future provider additions. |
| Weather | Open-Meteo | Completely free, no API key required, excellent UK coverage. Hourly forecast + current conditions. |
| Calendar | Google Calendar API | REST API, OAuth 2.0. Free. Official Python client library (`google-api-python-client`). Shared family Google Calendar. |

### Calendar

The shared family calendar is hosted in **Google Calendar**. Google's REST API and official Python client library (`google-api-python-client`) are used for all calendar access. Authentication is via OAuth 2.0 with a service account or installed app credentials stored in `.env`.

Family members can continue using the native iOS Calendar app — Google Calendar syncs to iOS via the Google account, so no change to day-to-day habits is required.

### Travel Feature — Implementation Detail

#### Commute schedule config

Routing is driven by `commute-schedule.json` (committed to the repo) combined with coordinate env vars. No routing logic is hardcoded.

**`commute-schedule.json` structure:**
```json
{
  "commuters": [
    {
      "name": "Ryan",
      "drop_order": ["dog", "nursery"],
      "schedule": {
        "monday":    { "mode": "office", "nursery_drop": true },
        "tuesday":   { "mode": "office", "nursery_drop": false },
        "wednesday": { "mode": "off",    "nursery_drop": false },
        "thursday":  { "mode": "office", "nursery_drop": true },
        "friday":    { "mode": "wfh",    "nursery_drop": false }
      }
    },
    {
      "name": "Emily",
      "drop_order": ["nursery", "dog"],
      "schedule": { ... }
    }
  ],
  "nursery": {
    "days": ["monday", "tuesday", "thursday"]
  },
  "dog_daycare": {
    "days": ["wednesday"],
    "weekly_dropper": "Ryan"
  }
}
```

`weekly_dropper` is the only field that needs editing week-to-week (when dog drop responsibility alternates).

**Day states per commuter:** `"office"` | `"wfh"` | `"off"`

**Drop gate rules:**
- Nursery drop only occurs if today is in `nursery.days` AND the commuter has `nursery_drop: true` in their schedule
- Dog drop only occurs if today is in `dog_daycare.days` AND the commuter matches `weekly_dropper`

#### Route data (Google Maps Routes API)

For each active commuter the backend resolves their waypoints and makes a single `computeRoutes` POST call with ordered waypoints and `computeAlternativeRoutes: true` (returns 2 route options).

**Waypoint ordering:**

| mode | drops | waypoints |
|---|---|---|
| office | none | home → work |
| office | [dog] | home → dog daycare → work |
| office | [nursery] | home → nursery → work |
| office | [dog, nursery] | home → dog daycare → nursery → work |
| wfh / off | none | *commuter omitted — no card* |
| wfh / off | [any] | home → [drops in drop_order] → home |

Drop order within a route follows the commuter's `drop_order` config.

From each route the backend extracts:

- `duration` (normalized to `travelTimeInSeconds`) — used for ETA display and delay status
- Traffic delay — computed as `duration - staticDuration`, used to determine colour state
- `staticDuration` (normalized to `noTrafficTravelTimeInSeconds`) — baseline for delay percentage calculation
- `distanceMeters` — shown as secondary info
- Road names extracted from step navigation instruction text (regex match on A/M road patterns) — joined to form a short description e.g. "via A3 and M25"

**Delay colour logic:**

| Condition | State |
|---|---|
| Delay < 10% above no-traffic time | Green |
| Delay 10–25% above no-traffic time | Amber |
| Delay > 25% above no-traffic time | Red |

#### Route description generation

The guidance instructions in the routing response include named road segments. The backend extracts the most significant road names (motorways and A-roads prioritised, limited to 2–3) and formats them as "via [Road1] and [Road2]". Generated server-side — no NLP required.

#### API response shape

```json
{
  "commuters": [
    {
      "name": "Ryan",
      "mode": "office",
      "drops": ["dog", "nursery"],
      "routes": [ ...2 alternatives... ],
      "incidents": [ ... ]
    }
  ],
  "is_stale": false
}
```

If both commuters are inactive (wfh/off with no drops), `commuters` is an empty array and the travel section is hidden on the frontend.

#### Incident warnings

Google Maps Routes API does not provide a traffic incident endpoint comparable to TomTom's `incidentDetails`. The `fetch_incidents` function returns an empty list for all calls. The incident display in the frontend remains in place — the warning list simply does not render when the array is empty (which is always the case with the current provider).

#### API request budget

With up to 2 active commuters polled every 2 minutes during a morning window (06:30–09:30):

| Call | Per cycle (2 commuters) | Daily count (3hr window) |
|---|---|---|
| `computeRoutes` (1 per active commuter) | up to 2 | up to ~180 |
| **Total** | | **up to ~180/day** |

This is well within Google's $200/month free credit. At standard Routes API pricing (~$0.005–0.01 per request), 180 requests/day costs less than $0.02/day. On days with one or both commuters inactive, the budget is lower. Outside the configured poll window, the backend serves the last cached result with a stale-data indicator on the frontend.

Add to `.env`:
```
POLL_WINDOW_START=06:30
POLL_WINDOW_END=09:30
```

---

## Tooling

### Backend (Python)

| Tool | Purpose |
|---|---|
| `pytest` | Unit and integration tests |
| `mutmut` | Mutation testing — verifies tests are meaningful, not just coverage theatre |
| `ruff` | Linting and code style enforcement |
| `pyproject.toml` | Project metadata, dependencies, and tool configuration |

### Frontend (React)

| Tool | Purpose |
|---|---|
| `Vitest` | Unit and component tests (shares Vite config, fast) |
| `React Testing Library` | Component behaviour testing |
| `Stryker` | Mutation testing — JavaScript/React ecosystem standard |
| `ESLint` | Linting and code standards (with React + hooks plugins) |
| `Prettier` | Code formatting |
| `package.json` | Project metadata, dependencies, and scripts |

---

## Claude Code Configuration

### Hooks

All hooks are configured in `.claude/settings.json` at the project root. They run as standalone shell processes outside the LLM — deterministic and fast. Hooks run synchronously, so keep individual hook execution under ~500ms; heavier operations (full test suite) belong on `Stop`, not `PostToolUse`.

`.claude/settings.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "comment": "Print git context and last test results at session open",
            "command": "echo '=== Session Start ===' && git status && git branch --show-current && echo '--- Last test results ---' && cat .last-test-results 2>/dev/null || echo 'No previous test results found'"
          }
        ]
      },
      {
        "hooks": [
          {
            "type": "command",
            "comment": "Install Python 3.14 + backend venv + frontend node_modules (web only)",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "comment": "Block edits to .env files",
            "command": "json=$(cat); file=$(echo \"$json\" | jq -r '.file_path // empty'); if [[ \"$file\" =~ \\.env ]]; then echo 'ERROR: Direct edits to .env are not permitted. Update .env.example and apply manually.'; exit 2; fi"
          },
          {
            "type": "command",
            "comment": "Block writes directly on main branch",
            "command": "branch=$(git branch --show-current); if [[ \"$branch\" == 'main' ]]; then echo 'ERROR: Direct writes to main are not permitted. Create a feature branch first.'; exit 2; fi"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "comment": "Block destructive shell commands",
            "command": "json=$(cat); cmd=$(echo \"$json\" | jq -r '.command // empty'); if echo \"$cmd\" | grep -qE 'rm -rf|git push --force|git reset --hard'; then echo \"ERROR: Destructive command blocked: $cmd\"; exit 2; fi"
          },
          {
            "type": "command",
            "comment": "Block direct pushes to main",
            "command": "json=$(cat); cmd=$(echo \"$json\" | jq -r '.command // empty'); if echo \"$cmd\" | grep -qE 'git push.*origin main|git push.*main'; then echo 'ERROR: Direct push to main blocked. Raise a PR instead.'; exit 2; fi"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "comment": "Auto-lint Python files on save",
            "command": "json=$(cat); file=$(echo \"$json\" | jq -r '.file_path // empty'); if [[ \"$file\" =~ \\.py$ ]]; then cd backend && ruff check --fix \"$file\" && ruff format \"$file\"; fi"
          },
          {
            "type": "command",
            "comment": "Auto-lint JS/JSX files on save",
            "command": "json=$(cat); file=$(echo \"$json\" | jq -r '.file_path // empty'); if [[ \"$file\" =~ \\.(jsx|js|ts|tsx)$ ]]; then cd frontend && npx eslint --fix \"$file\" && npx prettier --write \"$file\"; fi"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "hooks": [
          {
            "type": "command",
            "comment": "Log failures for post-session review",
            "command": "json=$(cat); echo \"[$(date -u +%Y-%m-%dT%H:%M:%SZ)] FAILURE: $(echo \"$json\" | jq -c '{tool: .tool_name, error: .error}')\" >> .claude-failures.jsonl"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "comment": "Run full test suite when Claude finishes a task",
            "command": "echo '--- Running full test suite ---' && cd backend && python -m pytest --tb=short 2>&1 | tee ../.last-test-results && cd ../frontend && npx vitest run 2>&1 | tee -a ../.last-test-results && echo '--- Test run complete ---'"
          }
        ]
      }
    ]
  }
}
```

**Hook summary:**

| Event | Matcher | Purpose |
|---|---|---|
| `SessionStart` | — | Print git status, current branch, last test results |
| `SessionStart` | — | Install Python 3.14 + venv + npm deps (web/cloud sessions only) |
| `PreToolUse` | Write/Edit | Block `.env` edits; block all writes on `main` |
| `PreToolUse` | Bash | Block `rm -rf`, `--force`, direct push to `main` |
| `PostToolUse` | Write/Edit | Auto-run `ruff` / `eslint` + `prettier` on changed file |
| `PostToolUseFailure` | — | Append failure details to `.claude-failures.jsonl` |
| `Stop` | — | Run full `pytest` + `vitest` suite; save to `.last-test-results` |

---

### Git and Branching Strategy

#### Branch model

```
main
  └── feature/travel-eta
  └── feature/weather-card
  └── feature/calendar-integration
  └── feature/alert-banner
```

- `main` is the only long-lived branch. It must always be deployable to the Pi.
- Every feature gets a short-lived `feature/<name>` branch cut from `main`.
- Branches are deleted after merge.
- The `PreToolUse` hook enforces this — Claude cannot write files or commit on `main` directly.

#### What Claude handles well

Claude Code is well-suited to:
- Creating feature branches and keeping commits clean and atomic
- Writing conventional commit messages (`feat:`, `fix:`, `test:`, `chore:`)
- Staging only relevant files — won't accidentally commit `.env`, `__pycache__`, etc.
- Rebasing a feature branch onto updated `main` when asked

#### What you own

- Reviewing the diff before merging (`git diff main..feature/X`)
- Raising the PR on GitHub — Claude will signal when a branch is ready but will not open a PR autonomously
- The merge itself — via GitHub PR UI or `git merge --no-ff` locally to preserve history
- Tagging releases when deploying to the Pi

#### Commit message convention

Use [Conventional Commits](https://www.conventionalcommits.org/) for a readable history:

```
feat(travel):     new feature on the travel integration
fix(weather):     bug fix on the weather card
test(calendar):   adding or updating tests
chore:            tooling, config, dependency updates
refactor:         code change that does not affect behaviour
```

---

### CLAUDE.md

Kept deliberately short — rules only for things Claude gets wrong or that need hard enforcement. Feature-specific context lives in `family-dashboard.md` and session prompts, not here.

```markdown
# Family Dashboard

Full spec: `family-dashboard.md`. Session prompts: `session-prompts.md`.

## Commands
- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Backend tests: `cd backend && python -m pytest --tb=short`
- Frontend tests: `cd frontend && npx vitest run`
- Lint check: `cd backend && ruff check . && cd ../frontend && npx eslint src/`

## MUST follow — build order
1. MUST write Gherkin feature file first, before any code
2. MUST write failing tests before implementation
3. MUST write minimum code to pass tests — nothing more
4. MUST run mutation tests after implementation; MUST NOT leave surviving mutants without documented justification
5. MUST confirm all tests pass before committing

## MUST follow — git
- MUST check current branch before starting: `git branch --show-current`
- MUST NEVER write files or commit on `main` — hooks enforce this and will block you
- MUST name branches `feature/<name>` cut from `main`
- MUST commit atomically with conventional commit messages after each logical step
- MUST inform the user when a feature is complete — NEVER merge or raise a PR autonomously

## NEVER do
- NEVER edit `.env` — hooks will block this; update `.env.example` instead
- NEVER run `rm -rf`, `git push --force`, or `git reset --hard` — hooks will block these
- NEVER run ruff or eslint manually — hooks run them automatically on file save
- NEVER implement behaviour not covered by a feature file

## Before writing any UI component
Invoke the `/frontend-design` skill and apply screen size design notes from `family-dashboard.md`.

## When compacting
Preserve: current branch name, list of modified files, last test run status, any surviving mutants noted.
```

---

## Build Order (Claude Code Instructions)

Claude Code must follow this sequence when implementing any feature. Do not skip or reorder steps.

### 1. Feature file first

Write a Gherkin `.feature` file describing the behaviour before any code is written. Feature files live in `features/`. They must describe user-visible or API-contract behaviour only — not implementation detail.

Example:
```gherkin
Feature: Travel ETA card
  Scenario: Route has significant delay
    Given the routing API returns a journey time 20% longer than the free-flow time
    When the dashboard renders the travel card
    Then the ETA card is shown in amber
    And the alert banner displays "Leave earlier — traffic on your route"
```

> **Note on the ClockCard:** The clock and date display is frontend-only — it reads the browser's local time via JavaScript (`new Date()`) and requires no backend endpoint. The feature file and tests should cover formatting correctness, 24-hour display, and date format (e.g. "Thursday 3 April"), not API integration.

### 2. Tests second

Write tests derived directly from the feature file before implementing the feature.

- **Backend:** `pytest` tests in `backend/tests/`
- **Frontend:** `Vitest` + React Testing Library tests in `frontend/src/**/*.test.jsx`

Tests must fail before the feature is implemented. Do not write tests that trivially pass against non-existent code.

### 3. Implementation last

Write the minimum code required to make the tests pass. Do not implement behaviour not covered by a test.

### 4. Mutation testing

After implementation, run mutation tests to verify the test suite is meaningful:

- **Backend:** `mutmut run` in `backend/`, then `mutmut results` — surviving mutants indicate undertested logic and must be addressed
- **Frontend:** `npx stryker run` in `frontend/` — review the HTML report; surviving mutants must be addressed

A passing test suite with surviving mutants is not acceptable. The goal is to kill all mutants or explicitly document why a surviving mutant is acceptable (e.g. a trivially unreachable branch).

### 5. Standards check

The `Stop` hook runs the full test suite automatically. Before marking a feature complete, confirm:
- All tests pass (`pytest` / `vitest run`)
- No ruff errors (`ruff check backend/`)
- No eslint errors (`cd frontend && npx eslint src/`)
- Mutation score is acceptable
- Branch is clean and commits are atomic with conventional messages

---

## Project Structure

```
family-dashboard/
├── .claude/
│   ├── settings.json                # Claude Code hooks (all hook config lives here)
│   └── hooks/
│       └── session-start.sh         # Web session env setup (Python 3.14 + deps; no-op locally)
├── .claude-failures.jsonl           # Auto-populated by PostToolUseFailure hook (gitignored)
├── .last-test-results               # Auto-populated by Stop hook (gitignored)
├── CLAUDE.md                        # Claude Code rules for this project
├── .env.example                     # Committed template — never commit .env itself
├── commute-schedule.json            # Weekly commute schedule (names, modes, drop assignments)
├── features/                        # Gherkin feature files (written before any code)
│   ├── clock.feature
│   ├── travel.feature
│   ├── travel_card.feature
│   ├── weather.feature
│   ├── weather_card.feature
│   ├── calendar.feature
│   ├── calendar_card.feature
│   ├── alert_banner.feature
│   ├── scheduler.feature
│   ├── dynamic_commutes.feature     # Per-commuter schedule-driven routing (backend)
│   └── dynamic_travel_card.feature  # Per-commuter cards and grid reflow (frontend)
├── backend/
│   ├── main.py                      # FastAPI app, routes, startup, serves frontend static files
│   ├── scheduler.py                 # Background polling / cache refresh tasks
│   ├── routers/
│   │   ├── travel.py                # Google Maps Routes API integration (per-commuter)
│   │   ├── weather.py               # Open-Meteo integration
│   │   └── calendar.py              # Google Calendar API integration
│   ├── services/
│   │   └── commute_schedule.py      # Schedule resolver — reads config, applies gates, builds waypoints
│   ├── config.py                    # Settings loaded from .env
│   ├── tests/
│   │   ├── test_travel.py
│   │   ├── test_commute_schedule.py
│   │   ├── test_travel_dynamic.py
│   │   ├── test_weather.py
│   │   └── test_calendar.py
│   ├── .env                         # API keys and config (gitignored — never commit)
│   └── pyproject.toml               # Project metadata, deps, ruff + pytest + mutmut config
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── components/
│   │       ├── ClockCard.jsx
│   │       ├── ClockCard.test.jsx
│   │       ├── TravelCard.jsx        # Per-commuter card; handles office and out-and-back routes
│   │       ├── TravelCard.test.jsx
│   │       ├── WeatherCard.jsx
│   │       ├── WeatherCard.test.jsx
│   │       ├── CalendarCard.jsx
│   │       ├── CalendarCard.test.jsx
│   │       ├── AlertBanner.jsx
│   │       └── AlertBanner.test.jsx
│   ├── index.html
│   ├── vite.config.js               # Proxies /api/* to FastAPI during dev
│   ├── stryker.config.json          # Stryker mutation testing config
│   ├── .eslintrc.js
│   ├── .prettierrc
│   └── package.json
└── family-dashboard.md              # This file — full project specification
```

---

## Configuration (.env)

Never commit `.env`. Commit `.env.example` with placeholder values only.

```
GOOGLE_MAPS_API_KEY=your_key_here

# Shared home location
HOME_LAT=51.XXXX
HOME_LON=-0.XXXX

# Per-commuter work locations
COMMUTER_1_WORK_LAT=51.XXXX
COMMUTER_1_WORK_LON=-0.XXXX
COMMUTER_2_WORK_LAT=51.XXXX
COMMUTER_2_WORK_LON=-0.XXXX

# Drop locations
NURSERY_LAT=51.XXXX
NURSERY_LON=-0.XXXX
DOG_DAYCARE_LAT=51.XXXX
DOG_DAYCARE_LON=-0.XXXX

# Google Calendar
GOOGLE_CALENDAR_ID=your_family_calendar_id@group.calendar.google.com

# Poll interval in seconds
POLL_INTERVAL_SECONDS=120

# Morning poll window (outside this window, cached data is served with a stale indicator)
POLL_WINDOW_START=06:30
POLL_WINDOW_END=09:30
```

Commuter names, schedules, drop assignments, and drop ordering are configured in `commute-schedule.json` (committed to the repo — no secrets). The `weekly_dropper` field in `dog_daycare` is the only entry that changes week-to-week.

---

## Development Workflow

1. **Build and test on laptop** — run FastAPI backend (`uvicorn main:app --reload`) and Vite dev server (`npm run dev`) concurrently; Vite proxies `/api/*` to FastAPI
2. **Follow build order** — feature file → tests → implementation → mutation tests → standards check, for every feature
3. **Follow git workflow** — feature branch per feature; conventional commits; no direct pushes to `main`
4. **Build for production** — `npm run build` outputs to `frontend/dist/`, FastAPI serves this as static files
5. **Deploy to Pi** — copy project over SSH, run backend as a systemd service
6. **Kiosk mode on Pi** — Chromium launches on boot in kiosk mode pointing at `localhost:8000`

### Pi Kiosk Boot Command (for reference)

```bash
chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:8000
```

---

## Display Schedule (Pi HDMI Control)

The display is on only during the morning window. A cron job on the Pi controls HDMI power via `vcgencmd` — no smart plug or additional hardware required.

Install the cron jobs after deploying to the Pi:

```bash
crontab -e
```

Add the following lines:

```cron
# Family dashboard display schedule
30 6 * * * /usr/bin/vcgencmd display_power 1   # Screen on at 06:30
0  9 * * * /usr/bin/vcgencmd display_power 0   # Screen off at 09:00
```

**Timing rationale:**
- **06:30 on** — aligns with the poll window start so live data is already cached when the screen comes on
- **09:00 off** — shortly after the morning rush ends; keeps the screen off for the rest of the day until requirements change

To adjust timings later, edit the cron entries. The poll window (`POLL_WINDOW_START` / `POLL_WINDOW_END` in `.env`) should be updated to match if the usage window changes.

To test manually:
```bash
vcgencmd display_power 0   # turn off
vcgencmd display_power 1   # turn on
```

---

## Raspberry Pi Setup Notes

- OS: **Raspberry Pi OS Bookworm** (64-bit, desktop)
- Python 3.14 via deadsnakes PPA (consistent with existing home automation project setup)
- Project lives in `~/projects/family-dashboard/`
- Virtual environment at `.venv`
- Systemd service to start the FastAPI backend on boot
- Chromium kiosk autostart after backend service is healthy

---

## Consistency with Existing Projects

This project follows the same conventions as the existing home automation scripts (`meal_planner.py`, `tesco_shop.py`):

- Python 3.14, `.venv`, `~/projects/` directory
- `python-dotenv` for secrets
- Explicit progress/status output
- Simple focused scripts with clear separation of concerns
- `CLAUDE.md` at project level for Claude Code context

---

## Future Enhancements

### MCP Server Integration

Once the core dashboard integrations (Google Maps Routes API, Open-Meteo, Google Calendar) are stable, consider wrapping them as **MCP (Model Context Protocol) servers** using the Anthropic mcp-builder skill (`/mnt/skills/examples/mcp-builder/SKILL.md`).

Benefits:
- Claude Code can call the live integrations directly during development and debugging
- Opens up conversational control — e.g. "What's traffic like on my commute right now?" or "Add nursery pickup to the family calendar for Friday"
- Fits naturally with the broader home automation project — the meal planner and Tesco scripts could eventually become MCP tools in the same server

This is a post-v1 concern. Build the dashboard working first, then consider MCP wrapping as a second phase.

### Traffic Incident Warnings

`fetch_incidents` currently returns an empty list — Google Maps Routes API (used for routing) does not expose a traffic incident endpoint. The frontend incident display is already in place and handles an empty array cleanly; route delay colours (green / amber / red) cover the primary signal.

When ready to add incidents, the recommended path is **HERE Traffic API**:

- Register free at `developer.here.com` (no credit card required)
- Free tier: 250,000 requests/month — well above dashboard usage
- Bounding-box incident query returns `category`, `description`, `criticality` (0–3), and `location` — structurally close to the TomTom shape that `parse_incidents` already handles
- Add `HERE_API_KEY` to `.env.example` and `config.py`
- Replace the stub in `fetch_incidents` (`routers/travel.py`) with a GET to `https://data.traffic.hereapi.com/v7/incidents` using the bounding box already calculated from route polyline points
- Update `parse_incidents` to map HERE's `criticality` → `magnitudeOfDelay`, `type` → `iconCategory`, `description.value` → `events[].description`, `location.description` → `from`

The National Highways Developer Portal (`developer.data.nationalhighways.co.uk`) is an alternative for UK motorway/A-road-only coverage with government data, but requires a more significant rewrite of `parse_incidents` to handle DATEX II JSON field names.