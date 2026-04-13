"""Background polling scheduler — polls APIs within the morning window and caches results."""

import asyncio
from datetime import datetime
from typing import Callable

from config import settings


def is_within_poll_window(now: datetime) -> bool:
    """Return True if now.time() falls within [poll_window_start, poll_window_end]."""
    current = now.time()
    return settings.poll_window_start <= current <= settings.poll_window_end


async def poll_once(
    fetch_travel: Callable,
    fetch_weather: Callable,
    fetch_calendar: Callable,
) -> None:
    """Fetch fresh data from all sources and update router module caches.

    Each fetcher is isolated — a failure in one does not prevent the others
    from running or updating their caches.
    """
    import routers.travel as travel_mod
    import routers.weather as weather_mod
    import routers.calendar as calendar_mod

    for fetch, mod, attr in (
        (fetch_travel, travel_mod, "_cache"),
        (fetch_weather, weather_mod, "_cache"),
        (fetch_calendar, calendar_mod, "_cache"),
    ):
        try:
            setattr(mod, attr, await fetch())
        except Exception:
            pass  # keep stale cache; logged at the source


async def poll_if_in_window(
    now: datetime,
    fetch_travel: Callable,
    fetch_weather: Callable,
    fetch_calendar: Callable,
) -> bool:
    """Poll only if now is within the configured window. Returns True if polled."""
    if not is_within_poll_window(now):
        return False
    await poll_once(fetch_travel, fetch_weather, fetch_calendar)
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

    while True:
        now = _get_now()
        try:
            await poll_if_in_window(now, fetch_travel, fetch_weather, fetch_calendar)
        except Exception:
            pass  # one bad cycle must not kill the scheduler task
        await asyncio.sleep(settings.poll_interval_seconds)
