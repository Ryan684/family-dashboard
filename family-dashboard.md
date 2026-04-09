# Family Morning Dashboard — Project Documentation

## Overview

A wall-mounted family dashboard designed to ease the morning routine. Displays live travel ETAs for commute routes, weather at relevant locations, and upcoming calendar events from a shared family calendar — all visible at a glance before leaving the house.

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
| Calendar | Apple iCloud CalDAV | CalDAV protocol via Python `caldav` library. App-specific password auth — no OAuth, no browser flow, no credentials file. Free. |

### Calendar

The shared family calendar is an **iCloud shared calendar**. The backend accesses it via the CalDAV protocol using the Python `caldav` library, connecting to Apple's CalDAV endpoint at `https://caldav.icloud.com`.

Authentication uses an app-specific password generated at appleid.apple.com → Sign-In and Security → App-Specific Passwords. No OAuth flow, no credentials file, no browser step — credentials are stored in `.env` and used directly.

Family members use the native iOS Calendar app as normal — the calendar remains an iCloud calendar, so no change to day-to-day habits is required.

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

All hooks are configured in `.claude/settings.json` at the project root. They run as standalone shell processes outside the LLM — deterministic and fast. Hooks run synchronously; keep individual hook execution under ~500ms.

| Event | Matcher | Purpose |

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

# Apple iCloud CalDAV
APPLE_CALDAV_URL=https://caldav.icloud.com
APPLE_CALDAV_USERNAME=your_apple_id_email
APPLE_CALDAV_PASSWORD=xxxx-xxxx-xxxx-xxxx
APPLE_CALDAV_CALENDAR_NAME=Family

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