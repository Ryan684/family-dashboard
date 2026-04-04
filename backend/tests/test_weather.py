"""Tests for weather backend — Open-Meteo integration."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app
from routers.weather import (
    find_current_hour_index,
    map_weather_code,
    parse_current,
    parse_forecast,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# map_weather_code
# ---------------------------------------------------------------------------


def test_map_weather_code_clear_sky():
    assert map_weather_code(0) == "Clear sky"


def test_map_weather_code_mainly_clear():
    assert map_weather_code(1) == "Mainly clear"


def test_map_weather_code_partly_cloudy():
    assert map_weather_code(2) == "Partly cloudy"


def test_map_weather_code_overcast():
    assert map_weather_code(3) == "Overcast"


def test_map_weather_code_fog():
    assert map_weather_code(45) == "Fog"


def test_map_weather_code_light_drizzle():
    assert map_weather_code(51) == "Light drizzle"


def test_map_weather_code_light_rain():
    assert map_weather_code(61) == "Light rain"


def test_map_weather_code_moderate_rain():
    assert map_weather_code(63) == "Moderate rain"


def test_map_weather_code_heavy_rain():
    assert map_weather_code(65) == "Heavy rain"


def test_map_weather_code_thunderstorm():
    assert map_weather_code(95) == "Thunderstorm"


def test_map_weather_code_unknown_fallback():
    assert map_weather_code(999) == "Unknown"


def test_map_weather_code_zero_is_not_unknown():
    # Ensures the dict lookup is used, not a fallback-only path
    assert map_weather_code(0) != "Unknown"


# ---------------------------------------------------------------------------
# parse_current
# ---------------------------------------------------------------------------


_CURRENT_DATA = {
    "time": "2025-01-01T08:00",
    "temperature_2m": 8.5,
    "apparent_temperature": 6.0,
    "weather_code": 61,
    "wind_speed_10m": 20.0,
    "relative_humidity_2m": 75,
}


def test_parse_current_temperature():
    result = parse_current(_CURRENT_DATA)
    assert result["temperature_celsius"] == 8.5


def test_parse_current_apparent_temperature():
    result = parse_current(_CURRENT_DATA)
    assert result["apparent_temperature_celsius"] == 6.0


def test_parse_current_weather_description():
    result = parse_current(_CURRENT_DATA)
    assert result["weather_description"] == "Light rain"


def test_parse_current_wind_speed():
    result = parse_current(_CURRENT_DATA)
    assert result["wind_speed_kmh"] == 20.0


def test_parse_current_humidity():
    result = parse_current(_CURRENT_DATA)
    assert result["humidity_percent"] == 75


def test_parse_current_missing_fields_default_to_none():
    result = parse_current({})
    assert result["temperature_celsius"] is None
    assert result["apparent_temperature_celsius"] is None
    assert result["wind_speed_kmh"] is None
    assert result["humidity_percent"] is None


def test_parse_current_missing_weather_code_defaults_to_clear_sky():
    result = parse_current({})
    assert result["weather_description"] == "Clear sky"


# ---------------------------------------------------------------------------
# find_current_hour_index
# ---------------------------------------------------------------------------


def test_find_current_hour_index_found_mid_list():
    times = ["2025-01-01T06:00", "2025-01-01T07:00", "2025-01-01T08:00"]
    assert find_current_hour_index(times, "2025-01-01T07:00") == 1


def test_find_current_hour_index_found_at_start():
    times = ["2025-01-01T06:00", "2025-01-01T07:00"]
    assert find_current_hour_index(times, "2025-01-01T06:00") == 0


def test_find_current_hour_index_found_at_end():
    times = ["2025-01-01T06:00", "2025-01-01T07:00", "2025-01-01T08:00"]
    assert find_current_hour_index(times, "2025-01-01T08:00") == 2


def test_find_current_hour_index_not_found_returns_zero():
    times = ["2025-01-01T06:00", "2025-01-01T07:00"]
    assert find_current_hour_index(times, "2025-01-01T12:00") == 0


def test_find_current_hour_index_empty_list_returns_zero():
    assert find_current_hour_index([], "2025-01-01T08:00") == 0


# ---------------------------------------------------------------------------
# parse_forecast
# ---------------------------------------------------------------------------


_HOURLY_DATA = {
    "time": [
        "2025-01-01T06:00",
        "2025-01-01T07:00",
        "2025-01-01T08:00",
        "2025-01-01T09:00",
        "2025-01-01T10:00",
        "2025-01-01T11:00",
        "2025-01-01T12:00",
        "2025-01-01T13:00",
    ],
    "temperature_2m": [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
    "weather_code": [0, 1, 2, 61, 63, 3, 0, 1],
    "precipitation_probability": [0, 0, 10, 50, 60, 20, 0, 5],
}


def test_parse_forecast_returns_six_entries_by_default():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    assert len(result) == 6


def test_parse_forecast_respects_start_index():
    result = parse_forecast(_HOURLY_DATA, start_index=2)
    assert result[0]["time"] == "2025-01-01T08:00"


def test_parse_forecast_temperature_first_entry():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    assert result[0]["temperature_celsius"] == 5.0


def test_parse_forecast_temperature_second_entry():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    assert result[1]["temperature_celsius"] == 6.0


def test_parse_forecast_weather_description_clear():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    assert result[0]["weather_description"] == "Clear sky"


def test_parse_forecast_weather_description_rain():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    assert result[3]["weather_description"] == "Light rain"


def test_parse_forecast_precipitation_zero():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    assert result[0]["precipitation_probability"] == 0


def test_parse_forecast_precipitation_nonzero():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    assert result[3]["precipitation_probability"] == 50


def test_parse_forecast_custom_count():
    result = parse_forecast(_HOURLY_DATA, start_index=0, count=3)
    assert len(result) == 3


def test_parse_forecast_clamps_to_available_data():
    # Only 2 entries available after start_index=6 (indices 6 and 7)
    result = parse_forecast(_HOURLY_DATA, start_index=6)
    assert len(result) == 2


def test_parse_forecast_entry_has_all_required_fields():
    result = parse_forecast(_HOURLY_DATA, start_index=0)
    entry = result[0]
    assert "time" in entry
    assert "temperature_celsius" in entry
    assert "weather_description" in entry
    assert "precipitation_probability" in entry


def test_parse_forecast_start_index_shifts_all_entries():
    result = parse_forecast(_HOURLY_DATA, start_index=1)
    assert result[0]["time"] == "2025-01-01T07:00"
    assert result[0]["temperature_celsius"] == 6.0


def test_parse_forecast_default_count_is_exactly_six():
    # Data has 7 entries; default count=6 must stop at 6, not 7
    data = {
        "time": ["t0", "t1", "t2", "t3", "t4", "t5", "t6"],
        "temperature_2m": [1.0] * 7,
        "weather_code": [0] * 7,
        "precipitation_probability": [0] * 7,
    }
    result = parse_forecast(data, start_index=0)
    assert len(result) == 6


def test_parse_forecast_missing_times_key_returns_empty():
    # Exercises the [] default on .get("time", []) — mutant changes it to None
    assert parse_forecast({}, start_index=0) == []


def test_parse_forecast_missing_temps_key_defaults_to_none():
    # Exercises the [] default on .get("temperature_2m", [])
    data = {
        "time": ["t0"],
        "weather_code": [0],
        "precipitation_probability": [0],
        # no temperature_2m key
    }
    result = parse_forecast(data, start_index=0, count=1)
    assert result[0]["temperature_celsius"] is None


def test_parse_forecast_missing_codes_key_defaults_to_clear_sky():
    # Exercises the [] default on .get("weather_code", []) and the 0 fallback
    data = {
        "time": ["t0"],
        "temperature_2m": [5.0],
        "precipitation_probability": [0],
        # no weather_code key
    }
    result = parse_forecast(data, start_index=0, count=1)
    assert result[0]["weather_description"] == "Clear sky"


def test_parse_forecast_missing_precip_key_defaults_to_zero():
    # Exercises the [] default on .get("precipitation_probability", []) and the 0 fallback
    data = {
        "time": ["t0"],
        "temperature_2m": [5.0],
        "weather_code": [0],
        # no precipitation_probability key
    }
    result = parse_forecast(data, start_index=0, count=1)
    assert result[0]["precipitation_probability"] == 0


def test_parse_forecast_short_temps_falls_back_to_none():
    # Exercises i < len(temps) guard — temps has fewer entries than times
    data = {
        "time": ["t0", "t1"],
        "temperature_2m": [5.0],  # only one entry; second access uses fallback
        "weather_code": [0, 0],
        "precipitation_probability": [0, 0],
    }
    result = parse_forecast(data, start_index=0, count=2)
    assert result[0]["temperature_celsius"] == 5.0
    assert result[1]["temperature_celsius"] is None


def test_parse_forecast_short_codes_falls_back_to_code_zero():
    # Exercises i < len(codes) guard and the 0 fallback value (not 1)
    data = {
        "time": ["t0", "t1"],
        "temperature_2m": [5.0, 6.0],
        "weather_code": [0],  # only one entry
        "precipitation_probability": [0, 0],
    }
    result = parse_forecast(data, start_index=0, count=2)
    assert result[1]["weather_description"] == "Clear sky"  # fallback code 0


def test_parse_forecast_short_precip_falls_back_to_zero():
    # Exercises i < len(precip) guard and the 0 fallback value (not 1)
    data = {
        "time": ["t0", "t1"],
        "temperature_2m": [5.0, 6.0],
        "weather_code": [0, 0],
        "precipitation_probability": [10],  # only one entry
    }
    result = parse_forecast(data, start_index=0, count=2)
    assert result[0]["precipitation_probability"] == 10
    assert result[1]["precipitation_probability"] == 0


# ---------------------------------------------------------------------------
# Shared mock response
# ---------------------------------------------------------------------------


_OPEN_METEO_RESPONSE = {
    "current": _CURRENT_DATA,
    "hourly": _HOURLY_DATA,
}


# ---------------------------------------------------------------------------
# Endpoint integration tests
# ---------------------------------------------------------------------------


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_returns_200(mock_fetch):
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    assert resp.status_code == 200


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_response_has_current_key(mock_fetch):
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    assert "current" in resp.json()


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_response_has_forecast_key(mock_fetch):
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    assert "forecast" in resp.json()


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_current_fields_present(mock_fetch):
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    current = resp.json()["current"]
    assert "temperature_celsius" in current
    assert "apparent_temperature_celsius" in current
    assert "weather_description" in current
    assert "wind_speed_kmh" in current
    assert "humidity_percent" in current


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_current_temperature_value(mock_fetch):
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    assert resp.json()["current"]["temperature_celsius"] == 8.5


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_current_weather_description(mock_fetch):
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    assert resp.json()["current"]["weather_description"] == "Light rain"


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_forecast_contains_six_entries(mock_fetch):
    # current time "2025-01-01T08:00" is at index 2; 6 entries remain (2–7)
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    assert len(resp.json()["forecast"]) == 6


@patch("routers.weather.fetch_weather", new_callable=AsyncMock)
def test_endpoint_forecast_first_entry_matches_current_hour(mock_fetch):
    mock_fetch.return_value = _OPEN_METEO_RESPONSE
    resp = client.get("/api/weather")
    assert resp.json()["forecast"][0]["time"] == "2025-01-01T08:00"
