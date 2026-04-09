"""Calendar router — iCloud CalDAV integration."""

import asyncio
import re
from datetime import date as _date
from datetime import datetime as _datetime
from datetime import timedelta

import caldav
import httpx
from fastapi import APIRouter

from config import settings
from routers.travel import extract_road_names, format_route_description

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

_cache: dict | None = None


def _get_today() -> _date:
    return _date.today()


def _format_datetime(dt: _datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.isoformat()


_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
_TRAVEL_FIELD_MASK = "routes.duration,routes.legs.steps.navigationInstruction"


def fetch_event_travel(
    location: str,
    home_lat: float,
    home_lon: float,
    api_key: str,
) -> dict | None:
    """Fetch driving duration from home to event location. Returns None on failure."""
    if not location or not api_key:
        return None

    body = {
        "origin": {"location": {"latLng": {"latitude": home_lat, "longitude": home_lon}}},
        "destination": {"address": location},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False,
    }

    try:
        resp = httpx.post(
            _ROUTES_URL,
            headers={"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": _TRAVEL_FIELD_MASK},
            json=body,
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    routes = data.get("routes", [])
    if not routes:
        return None

    route = routes[0]
    duration_str = route.get("duration", "0s")
    travel_secs = int(duration_str.rstrip("s")) if duration_str.endswith("s") else 0

    instructions = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            text = step.get("navigationInstruction", {}).get("instructions", "")
            for m in re.finditer(r"\b([AM]\d+\w*)\b", text):
                instructions.append({"roadName": m.group(1)})

    description = format_route_description(extract_road_names(instructions))
    return {"travel_time_seconds": travel_secs, "description": description}


def parse_event(component) -> dict:
    """Parse an icalendar VEVENT component into our event dict."""
    dtstart = component.get("dtstart").dt
    all_day = isinstance(dtstart, _date) and not isinstance(dtstart, _datetime)
    start_str = dtstart.isoformat() if all_day else _format_datetime(dtstart)
    return {
        "id": str(component.get("uid")),
        "summary": str(component.get("summary")),
        "start": start_str,
        "all_day": all_day,
        "calendar_color": "#4285F4",
    }


def _fetch_sync() -> dict:
    today = _get_today()
    tomorrow = today + timedelta(days=1)

    client = caldav.DAVClient(
        url=settings.apple_caldav_url,
        username=settings.apple_caldav_username,
        password=settings.apple_caldav_password,
    )
    principal = client.principal()
    calendars = principal.calendars()

    cal = next(
        (c for c in calendars if c.get_display_name() == settings.apple_caldav_calendar_name),
        None,
    )
    if cal is None:
        return {"today": [], "tomorrow": []}

    start_dt = _datetime.combine(today, _datetime.min.time())
    end_dt = _datetime.combine(tomorrow, _datetime.max.time())

    events = cal.date_search(start=start_dt, end=end_dt, expand=True)

    today_events: list[dict] = []
    tomorrow_events: list[dict] = []

    for event in events:
        component = event.icalendar_component
        status = component.get("status")
        if status and str(status).upper() == "CANCELLED":
            continue
        parsed = parse_event(component)
        location = component.get("location")
        parsed["travel"] = (
            fetch_event_travel(
                str(location),
                settings.home_lat,
                settings.home_lon,
                settings.google_maps_api_key,
            )
            if location
            else None
        )
        dtstart = component.get("dtstart").dt
        event_date = dtstart.date() if isinstance(dtstart, _datetime) else dtstart
        if event_date == today:
            today_events.append(parsed)
        elif event_date == tomorrow:
            tomorrow_events.append(parsed)

    return {"today": today_events, "tomorrow": tomorrow_events}


@router.get("")
async def get_calendar():
    from datetime import datetime

    from scheduler import is_within_poll_window as _scheduler_in_window

    is_stale = not _scheduler_in_window(datetime.now())
    if _cache is None:
        return {"today": [], "tomorrow": [], "is_stale": is_stale}
    return {**_cache, "is_stale": is_stale}


async def fetch_calendar_data() -> dict:
    """Fetch calendar events from iCloud CalDAV. Called by the scheduler."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch_sync)
