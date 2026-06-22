"""Tests for background polling scheduler."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from scheduler import (
    _should_poll_calendar,
    is_within_poll_window,
    is_within_weather_poll_window,
    poll_if_in_window,
    poll_once,
    run_scheduler,
)

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
# is_within_weather_poll_window (start shared with travel; end defaults 22:00)
# ---------------------------------------------------------------------------


def test_is_within_weather_poll_window_returns_true_inside():
    now = datetime(2025, 1, 1, 14, 0)
    assert is_within_weather_poll_window(now) is True


def test_is_within_weather_poll_window_returns_false_before_window():
    now = datetime(2025, 1, 1, 5, 0)
    assert is_within_weather_poll_window(now) is False


def test_is_within_weather_poll_window_returns_false_after_window():
    now = datetime(2025, 1, 1, 23, 0)
    assert is_within_weather_poll_window(now) is False


def test_is_within_weather_poll_window_true_at_start_boundary():
    now = datetime(2025, 1, 1, 6, 30)
    assert is_within_weather_poll_window(now) is True


def test_is_within_weather_poll_window_true_at_end_boundary():
    now = datetime(2025, 1, 1, 22, 0)
    assert is_within_weather_poll_window(now) is True


def test_is_within_weather_poll_window_true_after_travel_window_end():
    now = datetime(2025, 1, 1, 10, 0)
    assert is_within_weather_poll_window(now) is True


# ---------------------------------------------------------------------------
# poll_if_in_window — window enforcement
# ---------------------------------------------------------------------------


async def test_no_api_calls_outside_poll_window():
    mock_travel = AsyncMock()
    mock_weather = AsyncMock()
    outside = datetime(2025, 1, 1, 2, 0)

    result = await poll_if_in_window(outside, mock_travel, mock_weather, None)

    mock_travel.assert_not_called()
    mock_weather.assert_not_called()
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


async def test_weather_polled_after_travel_window_closes():
    mock_travel = AsyncMock()
    mock_weather = AsyncMock(return_value={"locations": []})
    after_travel = datetime(2025, 1, 1, 10, 0)  # after 09:30 travel end, before 22:00 weather end

    result = await poll_if_in_window(after_travel, mock_travel, mock_weather, None)

    mock_travel.assert_not_called()
    mock_weather.assert_called_once()
    assert result is True


async def test_calendar_polled_outside_travel_window():
    mock_travel = AsyncMock()
    mock_weather = AsyncMock(return_value={"locations": []})
    mock_calendar = AsyncMock(return_value={"today": [], "tomorrow": []})
    after_travel = datetime(2025, 1, 1, 10, 0)  # outside travel window (09:30), inside weather window

    result = await poll_if_in_window(after_travel, mock_travel, mock_weather, mock_calendar)

    mock_travel.assert_not_called()
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


@patch("scheduler.is_within_weather_poll_window", return_value=False)
def test_weather_endpoint_stale_flag_outside_weather_poll_window(_mock_window):
    import routers.weather as weather_mod

    weather_mod._cache = {"current": {}, "forecast": []}

    resp = client.get("/api/weather")

    assert resp.json()["is_stale"] is True
    weather_mod._cache = None  # cleanup


@patch("routers.weather._get_now")
def test_weather_endpoint_not_stale_between_travel_and_weather_windows(mock_now):
    import routers.weather as weather_mod

    weather_mod._cache = {"current": {}, "forecast": []}
    mock_now.return_value = datetime(2025, 1, 1, 14, 0)

    resp = client.get("/api/weather")

    assert resp.json()["is_stale"] is False
    weather_mod._cache = None  # cleanup


@patch("scheduler.is_within_weather_poll_window", return_value=False)
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


# ---------------------------------------------------------------------------
# _should_poll_calendar — pure interval check
# ---------------------------------------------------------------------------


def test_should_poll_calendar_true_when_never_polled():
    assert _should_poll_calendar(datetime(2025, 1, 1, 7, 30), None) is True


def test_should_poll_calendar_false_when_interval_not_elapsed():
    from datetime import timedelta

    now = datetime(2025, 1, 1, 7, 30)
    last = now - timedelta(seconds=100)
    assert _should_poll_calendar(now, last) is False


def test_should_poll_calendar_true_when_interval_elapsed():
    from datetime import timedelta

    now = datetime(2025, 1, 1, 7, 30)
    last = now - timedelta(seconds=1800)
    assert _should_poll_calendar(now, last) is True


def test_should_poll_calendar_true_at_exact_boundary():
    from datetime import timedelta

    now = datetime(2025, 1, 1, 7, 30)
    last = now - timedelta(seconds=1800)
    assert _should_poll_calendar(now, last) is True


# ---------------------------------------------------------------------------
# run_scheduler — startup fetch primes caches regardless of poll window
# ---------------------------------------------------------------------------


async def test_run_scheduler_primes_caches_on_startup():
    import asyncio

    mock_travel = AsyncMock(return_value={"commuters": []})
    mock_weather = AsyncMock(return_value={"current": {}, "forecast": []})
    mock_calendar = AsyncMock(return_value={"today": [], "tomorrow": []})

    async def mock_sleep(_):
        raise asyncio.CancelledError

    outside = datetime(2025, 1, 1, 2, 0)  # outside all poll windows

    with patch("asyncio.sleep", side_effect=mock_sleep):
        try:
            await run_scheduler(
                get_now=lambda: outside,
                fetch_travel=mock_travel,
                fetch_weather=mock_weather,
                fetch_calendar=mock_calendar,
            )
        except asyncio.CancelledError:
            pass

    mock_travel.assert_called_once()
    mock_weather.assert_called_once()
    mock_calendar.assert_called_once()


# ---------------------------------------------------------------------------
# run_scheduler — calendar interval throttling
# ---------------------------------------------------------------------------


async def test_calendar_not_polled_when_interval_not_elapsed():
    import asyncio

    calendar_args = []

    async def capturing_poll_if_in_window(now, ft, fw, fc):
        calendar_args.append(fc)
        raise asyncio.CancelledError

    fixed = datetime(2025, 1, 1, 7, 30)  # in travel window; time never advances

    with patch("scheduler.poll_if_in_window", side_effect=capturing_poll_if_in_window):
        try:
            await run_scheduler(
                get_now=lambda: fixed,
                fetch_travel=AsyncMock(return_value={"commuters": []}),
                fetch_weather=AsyncMock(return_value={"current": {}, "forecast": []}),
                fetch_calendar=AsyncMock(return_value={"today": [], "tomorrow": []}),
            )
        except asyncio.CancelledError:
            pass

    assert calendar_args[0] is None


async def test_calendar_polled_when_interval_elapsed():
    import asyncio
    from datetime import timedelta

    calendar_args = []

    async def capturing_poll_if_in_window(now, ft, fw, fc):
        calendar_args.append(fc)
        raise asyncio.CancelledError

    startup_time = datetime(2025, 1, 1, 7, 0)
    loop_time = startup_time + timedelta(seconds=1800)
    times = iter([startup_time, loop_time])

    with patch("scheduler.poll_if_in_window", side_effect=capturing_poll_if_in_window):
        try:
            await run_scheduler(
                get_now=lambda: next(times),
                fetch_travel=AsyncMock(return_value={"commuters": []}),
                fetch_weather=AsyncMock(return_value={"current": {}, "forecast": []}),
                fetch_calendar=AsyncMock(return_value={"today": [], "tomorrow": []}),
            )
        except (asyncio.CancelledError, StopIteration):
            pass

    assert calendar_args[0] is not None


# ---------------------------------------------------------------------------
# config — required env vars
# ---------------------------------------------------------------------------


async def test_run_scheduler_loop_passes_correct_fetchers_to_poll():
    """Loop must pass the real travel and weather fetchers; checks mutmut_26/27/28."""
    import asyncio

    mock_travel = AsyncMock(return_value={"commuters": []})
    mock_weather = AsyncMock(return_value={"current": {}, "forecast": []})
    mock_calendar = AsyncMock(return_value={"today": [], "tomorrow": []})

    sleep_calls = 0

    async def mock_sleep(_):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 1:
            raise asyncio.CancelledError

    inside = datetime(2025, 1, 1, 7, 30)

    with patch("asyncio.sleep", side_effect=mock_sleep):
        try:
            await run_scheduler(
                get_now=lambda: inside,
                fetch_travel=mock_travel,
                fetch_weather=mock_weather,
                fetch_calendar=mock_calendar,
            )
        except asyncio.CancelledError:
            pass

    import routers.travel as travel_mod
    import routers.weather as weather_mod

    # startup(1) + one loop cycle(1) = 2 calls each; mutations drop this to 1
    assert mock_travel.call_count >= 2
    assert mock_weather.call_count >= 2

    travel_mod._cache = None
    weather_mod._cache = None


async def test_calendar_last_poll_timestamp_reset_after_poll():
    """After a calendar poll, last_calendar_poll must be set to now; checks mutmut_34."""
    import asyncio
    from datetime import timedelta

    cycle = 0
    second_cycle_calendar_arg = []

    async def capturing_poll_if_in_window(now, ft, fw, fc):
        nonlocal cycle
        cycle += 1
        if cycle == 2:
            second_cycle_calendar_arg.append(fc)
            raise asyncio.CancelledError

    startup_time = datetime(2025, 1, 1, 7, 0)
    loop_time = startup_time + timedelta(seconds=1800)
    times = iter([startup_time, loop_time, loop_time])

    with patch("scheduler.poll_if_in_window", side_effect=capturing_poll_if_in_window), \
         patch("asyncio.sleep", new_callable=AsyncMock):
        try:
            await run_scheduler(
                get_now=lambda: next(times),
                fetch_travel=AsyncMock(return_value={"commuters": []}),
                fetch_weather=AsyncMock(return_value={"current": {}, "forecast": []}),
                fetch_calendar=AsyncMock(return_value={"today": [], "tomorrow": []}),
            )
        except (asyncio.CancelledError, StopIteration):
            pass

    # Second cycle: calendar was just polled at 7:30, so interval not yet elapsed → None
    assert second_cycle_calendar_arg[0] is None


def test_require_env_raises_when_absent():
    import os
    from unittest.mock import patch as mpatch

    from config import _require_env

    with mpatch.dict(os.environ, {}, clear=False):
        os.environ.pop("_TEST_MISSING_VAR_XYZ", None)
        with pytest.raises(ValueError, match="_TEST_MISSING_VAR_XYZ"):
            _require_env("_TEST_MISSING_VAR_XYZ")


def test_require_env_returns_value_when_present():
    import os
    from unittest.mock import patch as mpatch

    from config import _require_env

    with mpatch.dict(os.environ, {"_TEST_PRESENT_VAR": "hello"}):
        assert _require_env("_TEST_PRESENT_VAR") == "hello"
