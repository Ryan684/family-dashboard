"""Background polling scheduler — polls APIs within the morning window and caches results."""

import asyncio
from datetime import datetime
from typing import Callable

from config import settings


def is_within_poll_window(now: datetime) -> bool:
    """Return True if now.time() falls within [poll_window_start, poll_window_end]."""
    current = now.time()
    return settings.poll_window_start <= current <= settings.poll_window_end


def is_within_weather_poll_window(now: datetime) -> bool:
    """Return True if now.time() falls within [poll_window_start, weather_poll_window_end]."""
    current = now.time()
    return settings.poll_window_start <= current <= settings.weather_poll_window_end


async def poll_once(
    fetch_travel: Callable | None,
    fetch_weather: Callable | None,
    fetch_calendar: Callable | None,
) -> None:
    """Fetch fresh data from active sources and update router module caches.

    Each fetcher is isolated — a failure in one does not prevent the others
    from running or updating their caches. Pass None to skip a fetcher.
    """
    import routers.travel as travel_mod
    import routers.weather as weather_mod
    import routers.calendar as calendar_mod

    for fetch, mod, attr in (
        (fetch_travel, travel_mod, "_cache"),
        (fetch_weather, weather_mod, "_cache"),
        (fetch_calendar, calendar_mod, "_cache"),
    ):
        if fetch is None:
            continue
        try:
            setattr(mod, attr, await fetch())
        except Exception:
            pass  # keep stale cache; logged at the source


def _should_poll_calendar(now: datetime, last_poll: datetime | None) -> bool:
    """Return True if the calendar interval has elapsed since last_poll (or never polled)."""
    if last_poll is None:
        return True
    return (now - last_poll).total_seconds() >= settings.calendar_poll_interval_seconds


async def poll_if_in_window(
    now: datetime,
    fetch_travel: Callable,
    fetch_weather: Callable,
    fetch_calendar: Callable,
) -> bool:
    """Poll each source only within its own configured window.

    Travel and calendar share the commute window; weather uses its own
    (wider) window so temperature stays fresh throughout the day.
    Returns True if any source was polled.
    """
    in_travel_window = is_within_poll_window(now)
    in_weather_window = is_within_weather_poll_window(now)
    if not in_travel_window and not in_weather_window and fetch_calendar is None:
        return False
    await poll_once(
        fetch_travel if in_travel_window else None,
        fetch_weather if in_weather_window else None,
        fetch_calendar,
    )
    return True


async def run_scheduler(
    get_now: Callable[[], datetime] | None = None,
    fetch_travel: Callable | None = None,
    fetch_weather: Callable | None = None,
    fetch_calendar: Callable | None = None,
) -> None:
    """Background loop: poll every POLL_INTERVAL_SECONDS within the window."""
    if fetch_travel is None:
        from routers.travel import fetch_travel_data

        fetch_travel = fetch_travel_data
    if fetch_weather is None:
        from routers.weather import fetch_weather_data

        fetch_weather = fetch_weather_data
    if fetch_calendar is None:
        from routers.calendar import fetch_calendar_data

        fetch_calendar = fetch_calendar_data

    _get_now = get_now or datetime.now

    await poll_once(fetch_travel, fetch_weather, fetch_calendar)
    last_calendar_poll: datetime = _get_now()

    while True:
        now = _get_now()
        calendar_due = _should_poll_calendar(now, last_calendar_poll)
        try:
            await poll_if_in_window(
                now, fetch_travel, fetch_weather,
                fetch_calendar if calendar_due else None,
            )
        except Exception:
            pass  # one bad cycle must not kill the scheduler task
        if calendar_due:
            last_calendar_poll = now
        await asyncio.sleep(settings.poll_interval_seconds)
