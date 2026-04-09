"""Calendar router — iCloud CalDAV integration."""

import asyncio
from datetime import date as _date
from datetime import datetime as _datetime
from datetime import timedelta

import caldav
from fastapi import APIRouter

from config import settings

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

_cache: dict | None = None


def _get_today() -> _date:
    return _date.today()


def _format_datetime(dt: _datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt.isoformat()


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
