# Family Dashboard

A wall-mounted morning dashboard for a Raspberry Pi + touchscreen. Shows live commute ETAs for each active household member, current weather, and upcoming calendar events — all visible at a glance before leaving the house.

Full project spec and design rationale: [`family-dashboard.md`](family-dashboard.md)

---

## Prerequisites

- Python 3.14
- Node.js 20+
- A Google Cloud project with the [Routes API](https://console.cloud.google.com/apis/library/routes.googleapis.com) enabled and an API key
- A Google Calendar API project with OAuth credentials ([setup guide](https://developers.google.com/calendar/api/quickstart/python))

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
| `GOOGLE_CALENDAR_ID` | Yes | Your shared Google Calendar ID |
| `POLL_INTERVAL_SECONDS` | No | How often to refresh data (default: 120) |
| `POLL_WINDOW_START/END` | No | Morning window for live data (default: 06:30–09:30) |

Coordinates are decimal degrees (e.g. `51.5074`, `-0.1278`). Outside the poll window the backend serves the last cached result with a stale indicator.

### 3. Configure the commute schedule

Edit `commute-schedule.json` to match your household. This file controls who goes to the office, who works from home, and who does which school/daycare drops each day.

```json
{
  "commuters": [
    {
      "name": "YourName",
      "drop_order": ["dog", "nursery"],
      "schedule": {
        "monday":    { "mode": "office", "nursery_drop": true },
        "tuesday":   { "mode": "office", "nursery_drop": false },
        "wednesday": { "mode": "off",    "nursery_drop": false },
        "thursday":  { "mode": "office", "nursery_drop": true },
        "friday":    { "mode": "wfh",    "nursery_drop": false }
      }
    }
  ],
  "nursery": {
    "days": ["monday", "tuesday", "thursday"]
  },
  "dog_daycare": {
    "days": ["wednesday"],
    "weekly_dropper": "YourName"
  }
}
```

**Mode values:** `"office"` (routes to work), `"wfh"` or `"off"` (routes home after drops, or omitted if no drops).

**Drop gates:**
- Nursery drop only happens if today is in `nursery.days` AND `nursery_drop: true` for that commuter
- Dog drop only happens if today is in `dog_daycare.days` AND the commuter matches `weekly_dropper`

**`weekly_dropper`** is the only field that needs editing week-to-week when dog drop responsibility alternates.

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
- Recommended hardware (Pi 5 + 21–24" touchscreen monitor)
- Systemd service setup
- Chromium kiosk mode boot command
- Display on/off cron schedule
