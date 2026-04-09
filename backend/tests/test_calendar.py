"""Tests for the calendar backend — iCloud CalDAV integration."""

import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from icalendar import Event as ICalEvent

from main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = datetime.date(2026, 4, 9)
TOMORROW = TODAY + datetime.timedelta(days=1)


def _make_component(
    uid: str,
    summary: str,
    dtstart: datetime.date | datetime.datetime,
    status: str | None = None,
) -> ICalEvent:
    e = ICalEvent()
    e.add("uid", uid)
    e.add("summary", summary)
    e.add("dtstart", dtstart)
    if status:
        e.add("status", status)
    return e


def _make_caldav_event(
    uid: str,
    summary: str,
    dtstart: datetime.date | datetime.datetime,
    status: str | None = None,
) -> MagicMock:
    mock_event = MagicMock()
    mock_event.icalendar_component = _make_component(uid, summary, dtstart, status)
    return mock_event


_TEST_CALENDAR_NAME = "Family"


def _make_mock_settings() -> MagicMock:
    s = MagicMock()
    s.apple_caldav_url = "https://caldav.icloud.com"
    s.apple_caldav_username = "test@example.com"
    s.apple_caldav_password = "test-password"
    s.apple_caldav_calendar_name = _TEST_CALENDAR_NAME
    return s


def _make_mock_dav_client(events: list, calendar_name: str = _TEST_CALENDAR_NAME) -> MagicMock:
    mock_cal = MagicMock()
    mock_cal.get_display_name.return_value = calendar_name
    mock_cal.date_search.return_value = events

    mock_principal = MagicMock()
    mock_principal.calendars.return_value = [mock_cal]

    mock_client_instance = MagicMock()
    mock_client_instance.principal.return_value = mock_principal

    mock_dav_cls = MagicMock(return_value=mock_client_instance)
    return mock_dav_cls


def _fetch_sync_with_mocks(events: list, calendar_name: str = _TEST_CALENDAR_NAME) -> dict:
    """Run _fetch_sync with caldav, settings, and _get_today all mocked."""
    from routers.calendar import _fetch_sync

    mock_dav = _make_mock_dav_client(events, calendar_name)
    mock_settings = _make_mock_settings()
    mock_settings.apple_caldav_calendar_name = _TEST_CALENDAR_NAME

    with patch("caldav.DAVClient", mock_dav), patch(
        "routers.calendar.settings", mock_settings
    ), patch("routers.calendar._get_today", return_value=TODAY):
        return _fetch_sync()


# ---------------------------------------------------------------------------
# parse_event — timed events
# ---------------------------------------------------------------------------


def test_parse_event_returns_id():
    from routers.calendar import parse_event

    component = _make_component("uid-abc", "Meeting", datetime.datetime(2026, 4, 9, 9, 0))
    result = parse_event(component)
    assert result["id"] == "uid-abc"


def test_parse_event_returns_summary():
    from routers.calendar import parse_event

    component = _make_component("uid-1", "School run", datetime.datetime(2026, 4, 9, 8, 30))
    result = parse_event(component)
    assert result["summary"] == "School run"


def test_parse_event_timed_event_all_day_is_false():
    from routers.calendar import parse_event

    component = _make_component("uid-2", "Standup", datetime.datetime(2026, 4, 9, 9, 0))
    result = parse_event(component)
    assert result["all_day"] is False


def test_parse_event_timed_event_start_includes_time():
    from routers.calendar import parse_event

    component = _make_component("uid-3", "Dentist", datetime.datetime(2026, 4, 9, 14, 30))
    result = parse_event(component)
    assert "T" in result["start"]
    assert "14:30" in result["start"]


def test_parse_event_timed_event_start_is_iso_string():
    from routers.calendar import parse_event

    component = _make_component("uid-4", "Gym", datetime.datetime(2026, 4, 9, 7, 0))
    result = parse_event(component)
    # Should parse as a datetime without error
    datetime.datetime.fromisoformat(result["start"])


# ---------------------------------------------------------------------------
# parse_event — all-day events
# ---------------------------------------------------------------------------


def test_parse_event_all_day_event_all_day_is_true():
    from routers.calendar import parse_event

    component = _make_component("uid-5", "Bank holiday", datetime.date(2026, 4, 9))
    result = parse_event(component)
    assert result["all_day"] is True


def test_parse_event_all_day_event_start_has_no_time_component():
    from routers.calendar import parse_event

    component = _make_component("uid-6", "Holiday", datetime.date(2026, 4, 9))
    result = parse_event(component)
    assert "T" not in result["start"]


def test_parse_event_all_day_event_start_is_date_string():
    from routers.calendar import parse_event

    component = _make_component("uid-7", "Holiday", datetime.date(2026, 4, 9))
    result = parse_event(component)
    datetime.date.fromisoformat(result["start"])  # must not raise


# ---------------------------------------------------------------------------
# parse_event — calendar colour
# ---------------------------------------------------------------------------


def test_parse_event_returns_calendar_color():
    from routers.calendar import parse_event

    component = _make_component("uid-8", "Event", datetime.datetime(2026, 4, 9, 10, 0))
    result = parse_event(component)
    assert "calendar_color" in result
    assert result["calendar_color"].startswith("#")


# ---------------------------------------------------------------------------
# _fetch_sync — event bucketing
# ---------------------------------------------------------------------------


def test_fetch_sync_today_events_in_today_list():
    event = _make_caldav_event("e1", "Today meeting", datetime.datetime(2026, 4, 9, 9, 0))
    result = _fetch_sync_with_mocks([event])
    assert len(result["today"]) == 1
    assert result["today"][0]["summary"] == "Today meeting"


def test_fetch_sync_tomorrow_events_in_tomorrow_list():
    event = _make_caldav_event("e2", "Tomorrow meeting", datetime.datetime(2026, 4, 10, 10, 0))
    result = _fetch_sync_with_mocks([event])
    assert len(result["tomorrow"]) == 1
    assert result["tomorrow"][0]["summary"] == "Tomorrow meeting"


def test_fetch_sync_two_today_one_tomorrow():
    events = [
        _make_caldav_event("e1", "Morning", datetime.datetime(2026, 4, 9, 8, 0)),
        _make_caldav_event("e2", "Afternoon", datetime.datetime(2026, 4, 9, 15, 0)),
        _make_caldav_event("e3", "Tomorrow", datetime.datetime(2026, 4, 10, 9, 0)),
    ]
    result = _fetch_sync_with_mocks(events)
    assert len(result["today"]) == 2
    assert len(result["tomorrow"]) == 1


def test_fetch_sync_all_day_event_bucketed_to_today():
    event = _make_caldav_event("e4", "All day today", datetime.date(2026, 4, 9))
    result = _fetch_sync_with_mocks([event])
    assert len(result["today"]) == 1
    assert result["today"][0]["all_day"] is True


def test_fetch_sync_all_day_event_bucketed_to_tomorrow():
    event = _make_caldav_event("e5", "All day tomorrow", datetime.date(2026, 4, 10))
    result = _fetch_sync_with_mocks([event])
    assert len(result["tomorrow"]) == 1
    assert result["tomorrow"][0]["all_day"] is True


# ---------------------------------------------------------------------------
# parse_event — timezone-aware datetime
# ---------------------------------------------------------------------------


def test_parse_event_timezone_aware_datetime_stripped_to_naive():
    from routers.calendar import parse_event
    import zoneinfo

    tz = zoneinfo.ZoneInfo("Europe/London")
    aware_dt = datetime.datetime(2026, 4, 9, 9, 0, tzinfo=tz)
    component = _make_component("uid-tz", "TZ event", aware_dt)
    result = parse_event(component)
    # Result must be a parseable ISO string with no timezone suffix
    parsed = datetime.datetime.fromisoformat(result["start"])
    assert parsed.tzinfo is None


def test_parse_event_timezone_aware_utc_stripped_to_naive():
    from routers.calendar import parse_event

    utc_dt = datetime.datetime(2026, 4, 9, 8, 0, tzinfo=datetime.timezone.utc)
    component = _make_component("uid-utc", "UTC event", utc_dt)
    result = parse_event(component)
    parsed = datetime.datetime.fromisoformat(result["start"])
    assert parsed.tzinfo is None


# ---------------------------------------------------------------------------
# _fetch_sync — DAVClient constructor args
# ---------------------------------------------------------------------------


def test_fetch_sync_passes_url_to_dav_client():
    from routers.calendar import _fetch_sync

    mock_dav = _make_mock_dav_client([])
    mock_settings = _make_mock_settings()

    with patch("caldav.DAVClient", mock_dav), patch(
        "routers.calendar.settings", mock_settings
    ), patch("routers.calendar._get_today", return_value=TODAY):
        _fetch_sync()

    call_kwargs = mock_dav.call_args.kwargs
    assert call_kwargs["url"] == mock_settings.apple_caldav_url


def test_fetch_sync_passes_username_to_dav_client():
    from routers.calendar import _fetch_sync

    mock_dav = _make_mock_dav_client([])
    mock_settings = _make_mock_settings()

    with patch("caldav.DAVClient", mock_dav), patch(
        "routers.calendar.settings", mock_settings
    ), patch("routers.calendar._get_today", return_value=TODAY):
        _fetch_sync()

    call_kwargs = mock_dav.call_args.kwargs
    assert call_kwargs["username"] == mock_settings.apple_caldav_username


def test_fetch_sync_passes_password_to_dav_client():
    from routers.calendar import _fetch_sync

    mock_dav = _make_mock_dav_client([])
    mock_settings = _make_mock_settings()

    with patch("caldav.DAVClient", mock_dav), patch(
        "routers.calendar.settings", mock_settings
    ), patch("routers.calendar._get_today", return_value=TODAY):
        _fetch_sync()

    call_kwargs = mock_dav.call_args.kwargs
    assert call_kwargs["password"] == mock_settings.apple_caldav_password


# ---------------------------------------------------------------------------
# _fetch_sync — cancelled events
# ---------------------------------------------------------------------------


def test_fetch_sync_cancelled_event_excluded():
    event = _make_caldav_event(
        "e6", "Cancelled meeting", datetime.datetime(2026, 4, 9, 11, 0), status="CANCELLED"
    )
    result = _fetch_sync_with_mocks([event])
    assert result["today"] == []
    assert result["tomorrow"] == []


def test_fetch_sync_event_without_status_not_excluded():
    # An event with no STATUS field must NOT be treated as cancelled
    event = _make_caldav_event("e-nostatus", "Regular event", datetime.datetime(2026, 4, 9, 9, 0))
    result = _fetch_sync_with_mocks([event])
    assert len(result["today"]) == 1


def test_fetch_sync_event_with_confirmed_status_not_excluded():
    # STATUS: CONFIRMED is not CANCELLED — must NOT be excluded
    # Guards against `status and` → `status or` mutation: with `or`, a truthy non-CANCELLED
    # status would incorrectly cause the event to be skipped
    event = _make_caldav_event(
        "e-confirmed", "Confirmed event", datetime.datetime(2026, 4, 9, 9, 0), status="CONFIRMED"
    )
    result = _fetch_sync_with_mocks([event])
    assert len(result["today"]) == 1
    assert result["today"][0]["summary"] == "Confirmed event"


def test_fetch_sync_cancelled_first_active_second_active_still_included():
    # Cancelled event comes BEFORE active event — guards against `break` replacing `continue`
    events = [
        _make_caldav_event("e-cancel", "Cancelled", datetime.datetime(2026, 4, 9, 9, 0), status="CANCELLED"),
        _make_caldav_event("e-active", "Active after cancel", datetime.datetime(2026, 4, 9, 10, 0)),
    ]
    result = _fetch_sync_with_mocks(events)
    assert len(result["today"]) == 1
    assert result["today"][0]["summary"] == "Active after cancel"


def test_fetch_sync_mixed_cancelled_and_active():
    events = [
        _make_caldav_event("e7", "Active", datetime.datetime(2026, 4, 9, 9, 0)),
        _make_caldav_event("e8", "Cancelled", datetime.datetime(2026, 4, 9, 10, 0), status="CANCELLED"),
    ]
    result = _fetch_sync_with_mocks(events)
    assert len(result["today"]) == 1
    assert result["today"][0]["summary"] == "Active"


# ---------------------------------------------------------------------------
# _fetch_sync — no events / calendar not found
# ---------------------------------------------------------------------------


def test_fetch_sync_no_events_returns_empty_lists():
    result = _fetch_sync_with_mocks([])
    assert result == {"today": [], "tomorrow": []}


def test_fetch_sync_calendar_not_found_returns_empty_lists():
    # Mock server returns a calendar with a different name → cal is None → empty
    result = _fetch_sync_with_mocks([], calendar_name="Other Calendar")
    assert result == {"today": [], "tomorrow": []}


def test_fetch_sync_result_has_today_and_tomorrow_keys():
    result = _fetch_sync_with_mocks([])
    assert "today" in result
    assert "tomorrow" in result


# ---------------------------------------------------------------------------
# GET /api/calendar endpoint
# ---------------------------------------------------------------------------


@patch("routers.calendar._cache", {"today": [], "tomorrow": []})
def test_endpoint_returns_200():
    with patch("scheduler.is_within_poll_window", return_value=True):
        resp = client.get("/api/calendar")
    assert resp.status_code == 200


@patch("routers.calendar._cache", {"today": [], "tomorrow": []})
def test_endpoint_response_has_today_key():
    with patch("scheduler.is_within_poll_window", return_value=True):
        resp = client.get("/api/calendar")
    assert "today" in resp.json()


@patch("routers.calendar._cache", {"today": [], "tomorrow": []})
def test_endpoint_response_has_tomorrow_key():
    with patch("scheduler.is_within_poll_window", return_value=True):
        resp = client.get("/api/calendar")
    assert "tomorrow" in resp.json()


@patch("routers.calendar._cache", {"today": [], "tomorrow": []})
def test_endpoint_response_has_is_stale_key():
    with patch("scheduler.is_within_poll_window", return_value=True):
        resp = client.get("/api/calendar")
    assert "is_stale" in resp.json()


def test_endpoint_empty_cache_returns_empty_lists():
    import routers.calendar as cal_mod

    original = cal_mod._cache
    cal_mod._cache = None
    try:
        with patch("scheduler.is_within_poll_window", return_value=True):
            resp = client.get("/api/calendar")
        assert resp.json()["today"] == []
        assert resp.json()["tomorrow"] == []
    finally:
        cal_mod._cache = original


def test_endpoint_outside_window_is_stale_true():
    import routers.calendar as cal_mod

    original = cal_mod._cache
    cal_mod._cache = {"today": [], "tomorrow": []}
    try:
        with patch("scheduler.is_within_poll_window", return_value=False):
            resp = client.get("/api/calendar")
        assert resp.json()["is_stale"] is True
    finally:
        cal_mod._cache = original


def test_endpoint_inside_window_is_stale_false():
    import routers.calendar as cal_mod

    original = cal_mod._cache
    cal_mod._cache = {"today": [], "tomorrow": []}
    try:
        with patch("scheduler.is_within_poll_window", return_value=True):
            resp = client.get("/api/calendar")
        assert resp.json()["is_stale"] is False
    finally:
        cal_mod._cache = original


def test_endpoint_cached_events_returned():
    import routers.calendar as cal_mod

    cached = {
        "today": [
            {
                "id": "evt-1",
                "summary": "Morning standup",
                "start": "2026-04-09T09:00:00",
                "all_day": False,
                "calendar_color": "#4285F4",
            }
        ],
        "tomorrow": [],
    }
    original = cal_mod._cache
    cal_mod._cache = cached
    try:
        with patch("scheduler.is_within_poll_window", return_value=True):
            resp = client.get("/api/calendar")
        assert resp.json()["today"][0]["summary"] == "Morning standup"
    finally:
        cal_mod._cache = original
