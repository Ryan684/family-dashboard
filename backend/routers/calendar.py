# Calendar router — Google Calendar API integration
from fastapi import APIRouter

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

# Module-level cache: holds last successful response dict
_cache: dict | None = None


@router.get("")
async def get_calendar():
    from scheduler import is_within_poll_window as _scheduler_in_window
    from datetime import datetime

    is_stale = not _scheduler_in_window(datetime.now())
    if _cache is None:
        return {"today": [], "tomorrow": [], "is_stale": is_stale}
    return {**_cache, "is_stale": is_stale}


async def fetch_calendar_data() -> dict:
    """Fetch calendar events. Called by the scheduler. (Stub — full implementation pending.)"""
    return {"today": [], "tomorrow": []}
