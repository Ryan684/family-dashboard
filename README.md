# Family Dashboard

A wall-mounted morning dashboard for a Raspberry Pi 5 + Official Raspberry Pi Monitor SC0940 (15.6"). Shows live commute ETAs for each active household member, current weather, and upcoming calendar events — all visible at a glance before leaving the house.

Full project spec and design rationale: [`family-dashboard.md`](family-dashboard.md)

---

## Prerequisites

- Python 3.14
- Node.js 20+
- A Google Cloud project with the [Routes API](https://console.cloud.google.com/apis/library/routes.googleapis.com) enabled and an API key
- An Apple ID with access to the shared iCloud calendar, and an app-specific password (generate at appleid.apple.com → Sign-In and Security → App-Specific Passwords)

---

## Setup

### 1. Clone and create the virtual environment

```bash
git clone <repo-url>
cd family-dashboard
cd backend && python3.14 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd ../frontend && npm install
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_MAPS_API_KEY` | Yes | Google Cloud API key with Routes API enabled |
| `HOME_LAT` / `HOME_LON` | Yes | Your home coordinates |
| `COMMUTER_1_WORK_LAT/LON` | Yes | Work location for the first commuter |
| `COMMUTER_2_WORK_LAT/LON` | If 2 commuters | Work location for the second commuter |
| `NURSERY_LAT/LON` | If nursery drops | Nursery coordinates |
| `DOG_DAYCARE_LAT/LON` | If dog drops | Dog daycare coordinates |
| `APPLE_CALDAV_URL` | Yes | iCloud CalDAV endpoint (`https://caldav.icloud.com`) |
| `APPLE_CALDAV_USERNAME` | Yes | Your Apple ID email address |
| `APPLE_CALDAV_PASSWORD` | Yes | App-specific password from appleid.apple.com |
| `APPLE_CALDAV_CALENDAR_NAME` | Yes | Name of the shared calendar (e.g. `Family`) |
| `POLL_INTERVAL_SECONDS` | No | How often travel and weather tick (default: 120 s) |
| `POLL_WINDOW_START/END` | No | Morning window for travel and calendar live data (default: 06:30–09:30) |
| `WEATHER_POLL_WINDOW_END` | **Yes** | End of weather polling window — no default, must be set (e.g. `22:00`) |
| `CALENDAR_POLL_INTERVAL_SECONDS` | **Yes** | Re-fetch calendar this often within the travel window — no default (e.g. `1800`) |

Coordinates are decimal degrees (e.g. `51.5074`, `-0.1278`). Travel and calendar stop refreshing outside their poll window. Weather refreshes from `POLL_WINDOW_START` until `WEATHER_POLL_WINDOW_END` — Open-Meteo is free with no API key, so extending the weather window all day has no cost impact. All caches are primed immediately on startup so the dashboard is never empty after a service restart.

### 3. Configure the commute schedule

Edit `commute-schedule.json` to match your household. This file controls who goes to the office, who works from home, and who does which school/daycare drops each day.

```json
{
  "commuters": [
    {
      "name": "YourName",
      "drop_order": ["dog", "nursery"],
      "schedule": {
        "monday":    { "mode": "office", "nursery_drop": true,  "dog_drop": false, "departure_time": "07:30" },
        "tuesday":   { "mode": "office", "nursery_drop": false, "dog_drop": false, "departure_time": "08:00" },
        "wednesday": { "mode": "off",    "nursery_drop": false, "dog_drop": true },
        "thursday":  { "mode": "office", "nursery_drop": true,  "dog_drop": false, "departure_time": "07:30" },
        "friday":    { "mode": "wfh",    "nursery_drop": false, "dog_drop": false }
      }
    }
  ],
  "nursery": {
    "days": ["monday", "tuesday", "thursday"]
  },
  "dog_daycare": {
    "days": ["wednesday"]
  }
}
```

**Mode values:** `"office"` (routes to work), `"wfh"` or `"off"` (routes home after drops, or omitted if no drops).

**Drop gates:**
- Nursery drop only happens if today is in `nursery.days` AND `nursery_drop: true` for that commuter
- Dog drop only happens if today is in `dog_daycare.days` AND `dog_drop: true` for that commuter

**`dog_drop`** and **`nursery_drop`** work identically — set `true` on the days each commuter does that drop. To change who does the dog drop in a given week, flip the `dog_drop` flag on the relevant days for each commuter.

See [`family-dashboard.md`](family-dashboard.md#commute-schedule-config) for full routing logic and waypoint ordering.

---

## Running locally

In two terminals:

```bash
# Terminal 1 — backend
cd backend && source .venv/bin/activate
uvicorn main:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

The Vite dev server proxies `/api/*` to the FastAPI backend. Open `http://localhost:5173`.

---

## Tests

```bash
# Backend
cd backend && python -m pytest --tb=short

# Frontend
cd frontend && npx vitest run

# Mutation testing (backend)
cd backend && mutmut run && mutmut results

# Mutation testing (frontend)
cd frontend && npx stryker run
```

---

## Deploying to a Raspberry Pi

See [`family-dashboard.md`](family-dashboard.md) for:
- Recommended hardware (Pi 5 + 15.6" touchscreen monitor)
- Systemd service setup
- Chromium kiosk mode boot command
- Display on/off cron schedule
