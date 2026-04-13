"""Tests for background polling scheduler."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from scheduler import is_within_poll_window, poll_if_in_window, poll_once, run_scheduler

client = TestClient(app)


# ---------------------------------------------------------------------------
# is_within_poll_window (uses settings defaults: 06:30–09:30)
# ---------------------------------------------------------------------------


def test_is_within_poll_window_returns_true_inside():
    now = datetime(2025, 1, 1, 7, 30)
    assert is_within_poll_window(now) is True


def test_is_within_poll_window_returns_false_before_window():
    now = datetime(2025, 1, 1, 5, 0)
    assert is_within_poll_window(now) is False


def test_is_within_poll_window_returns_false_after_window():
    now = datetime(2025, 1, 1, 2, 0)
    assert is_within_poll_window(now) is False


def test_is_within_poll_window_true_at_start_boundary():
    now = datetime(2025, 1, 1, 6, 30)
    assert is_within_poll_window(now) is True


def test_is_within_poll_window_true_at_end_boundary():
    now = datetime(2025, 1, 1, 9, 30)
    assert is_within_poll_window(now) is True


# ---------------------------------------------------------------------------
# poll_if_in_window — window enforcement
# ---------------------------------------------------------------------------


async def test_no_api_calls_outside_poll_window():
    mock_travel = AsyncMock()
    mock_weather = AsyncMock()
    mock_calendar = AsyncMock()
    outside = datetime(2025, 1, 1, 2, 0)

    result = await poll_if_in_window(outside, mock_travel, mock_weather, mock_calendar)

    mock_travel.assert_not_called()
    mock_weather.assert_not_called()
    mock_calendar.assert_not_called()
    assert result is False


async def test_api_calls_made_inside_poll_window():
    mock_travel = AsyncMock(
        return_value={"commuters": []}
    )
    mock_weather = AsyncMock(return_value={"current": {}, "forecast": []})
    mock_calendar = AsyncMock(return_value={"today": [], "tomorrow": []})
    inside = datetime(2025, 1, 1, 7, 30)

    result = await poll_if_in_window(inside, mock_travel, mock_weather, mock_calendar)

    mock_travel.assert_called_once()
    mock_weather.assert_called_once()
    mock_calendar.assert_called_once()
    assert result is True


# ---------------------------------------------------------------------------
# poll_once — cache update
# ---------------------------------------------------------------------------


async def test_poll_once_updates_travel_cache():
    import routers.travel as travel_mod

    expected = {"commuters": [{"name": "Ryan", "mode": "office", "drops": [], "routes": [{"travel_time_seconds": 900}], "incidents": []}]}
    mock_travel = AsyncMock(return_value=expected)
    mock_weather = AsyncMock(return_value={"current": {}, "forecast": []})
    mock_calendar = AsyncMock(return_value={"today": [], "tomorrow": []})

    await poll_once(mock_travel, mock_weather, mock_calendar)

    assert travel_mod._cache == expected
    travel_mod._cache = None  # cleanup


async def test_poll_once_updates_weather_cache():
    import routers.weather as weather_mod

    expected = {"current": {"temperature_celsius": 10.0}, "forecast": []}
    mock_travel = AsyncMock(
        return_value={"commuters": []}
    )
    mock_weather = AsyncMock(return_value=expected)
    mock_calendar = AsyncMock(return_value={"today": [], "tomorrow": []})

    await poll_once(mock_travel, mock_weather, mock_calendar)

    assert weather_mod._cache == expected
    weather_mod._cache = None  # cleanup


async def test_poll_once_updates_calendar_cache():
    import routers.calendar as calendar_mod

    expected = {"today": [{"title": "School run"}], "tomorrow": []}
    mock_travel = AsyncMock(
        return_value={"commuters": []}
    )
    mock_weather = AsyncMock(return_value={"current": {}, "forecast": []})
    mock_calendar = AsyncMock(return_value=expected)

    await poll_once(mock_travel, mock_weather, mock_calendar)

    assert calendar_mod._cache == expected
    calendar_mod._cache = None  # cleanup


# ---------------------------------------------------------------------------
# Travel endpoint — cache serving and stale flag
# ---------------------------------------------------------------------------


@patch("routers.travel._get_now")
def test_travel_endpoint_serves_cached_data(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = {
        "commuters": [{"name": "Ryan", "mode": "office", "drops": [], "routes": [{"travel_time_seconds": 1200}], "incidents": []}],
    }
    mock_now.return_value = datetime(2025, 1, 1, 7, 30)

    resp = client.get("/api/travel")

    assert resp.status_code == 200
    assert resp.json()["commuters"][0]["routes"][0]["travel_time_seconds"] == 1200
    travel_mod._cache = None  # cleanup


@patch("scheduler.is_within_poll_window", return_value=False)
def test_travel_endpoint_stale_flag_outside_poll_window(_mock_window):
    import routers.travel as travel_mod

    travel_mod._cache = {"home_to_work": [], "home_to_nursery": [], "incidents": []}

    resp = client.get("/api/travel")

    assert resp.json()["is_stale"] is True
    travel_mod._cache = None  # cleanup


@patch("routers.travel._get_now")
def test_travel_endpoint_not_stale_inside_poll_window(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = {"home_to_work": [], "home_to_nursery": [], "incidents": []}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30)

    resp = client.get("/api/travel")

    assert resp.json()["is_stale"] is False
    travel_mod._cache = None  # cleanup


@patch("scheduler.is_within_poll_window", return_value=False)
def test_travel_endpoint_returns_empty_defaults_when_no_cache(_mock_window):
    import routers.travel as travel_mod

    travel_mod._cache = None

    resp = client.get("/api/travel")

    assert resp.status_code == 200
    assert resp.json()["commuters"] == []
    assert resp.json()["is_stale"] is True


# ---------------------------------------------------------------------------
# Weather endpoint — cache serving and stale flag
# ---------------------------------------------------------------------------


@patch("routers.weather._get_now")
def test_weather_endpoint_serves_cached_data(mock_now):
    import routers.weather as weather_mod

    weather_mod._cache = {
        "current": {"temperature_celsius": 12.5},
        "forecast": [],
    }
    mock_now.return_value = datetime(2025, 1, 1, 7, 30)

    resp = client.get("/api/weather")

    assert resp.status_code == 200
    assert resp.json()["current"]["temperature_celsius"] == 12.5
    weather_mod._cache = None  # cleanup


@patch("scheduler.is_within_poll_window", return_value=False)
def test_weather_endpoint_stale_flag_outside_poll_window(_mock_window):
    import routers.weather as weather_mod

    weather_mod._cache = {"current": {}, "forecast": []}

    resp = client.get("/api/weather")

    assert resp.json()["is_stale"] is True
    weather_mod._cache = None  # cleanup


@patch("scheduler.is_within_poll_window", return_value=False)
def test_weather_endpoint_returns_empty_defaults_when_no_cache(_mock_window):
    import routers.weather as weather_mod

    weather_mod._cache = None

    resp = client.get("/api/weather")

    assert resp.status_code == 200
    assert resp.json()["is_stale"] is True
    weather_mod._cache = None  # cleanup


# ---------------------------------------------------------------------------
# poll_once — resilience: one fetcher failure does not skip others
# ---------------------------------------------------------------------------


async def test_poll_once_updates_remaining_caches_when_weather_raises():
    import routers.calendar as calendar_mod
    import routers.travel as travel_mod
    import routers.weather as weather_mod

    travel_data = {"commuters": []}
    calendar_data = {"today": [], "tomorrow": []}
    stale_weather = {"current": {"temperature_celsius": 5.0}, "forecast": []}

    weather_mod._cache = stale_weather

    mock_travel = AsyncMock(return_value=travel_data)
    mock_weather = AsyncMock(side_effect=Exception("ReadTimeout"))
    mock_calendar = AsyncMock(return_value=calendar_data)

    await poll_once(mock_travel, mock_weather, mock_calendar)

    assert travel_mod._cache == travel_data
    assert calendar_mod._cache == calendar_data
    assert weather_mod._cache == stale_weather  # unchanged — kept stale value

    travel_mod._cache = None
    calendar_mod._cache = None
    weather_mod._cache = None


# ---------------------------------------------------------------------------
# run_scheduler — resilience: loop survives a failed poll cycle
# ---------------------------------------------------------------------------


async def test_run_scheduler_continues_after_failed_poll_cycle():
    call_count = 0

    async def mock_poll_if_in_window(now, fetch_travel, fetch_weather, fetch_calendar):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("simulated poll failure")

    sleep_count = 0

    async def mock_sleep(_):
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count >= 2:
            raise asyncio.CancelledError

    import asyncio

    with patch("scheduler.poll_if_in_window", side_effect=mock_poll_if_in_window), \
         patch("asyncio.sleep", side_effect=mock_sleep):
        try:
            await run_scheduler(
                get_now=lambda: datetime(2025, 1, 1, 7, 30),
                fetch_travel=AsyncMock(),
                fetch_weather=AsyncMock(),
                fetch_calendar=AsyncMock(),
            )
        except asyncio.CancelledError:
            pass

    assert call_count == 2
