"""Tests for weather backend — Open-Meteo integration."""

from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from routers.weather import (
    map_weather_code,
    parse_current,
    parse_daily_high,
    parse_daily_rainfall,
    parse_location_name,
    resolve_weather_locations,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _MockSettings:
    home_lat = 51.5
    home_lon = -0.1
    commuter_1_work_lat = 51.6
    commuter_1_work_lon = -0.2
    commuter_2_work_lat = 51.7
    commuter_2_work_lon = -0.3


_MOCK_SETTINGS = _MockSettings()

_TEST_SCHEDULE = {
    "commuters": [
        {
            "name": "Ryan",
            "drop_order": [],
            "schedule": {
                "monday": {"mode": "office", "nursery_drop": False},
                "tuesday": {"mode": "wfh", "nursery_drop": False},
                "wednesday": {"mode": "off", "nursery_drop": False},
                "thursday": {"mode": "office", "nursery_drop": False},
            },
        },
        {
            "name": "Robyn",
            "drop_order": [],
            "schedule": {
                "monday": {"mode": "office", "nursery_drop": False},
                "tuesday": {"mode": "off", "nursery_drop": False},
                "wednesday": {"mode": "wfh", "nursery_drop": False},
                "thursday": {"mode": "wfh", "nursery_drop": False},
            },
        },
    ],
    "nursery": {"days": []},
    "dog_daycare": {"days": [], "weekly_dropper": ""},
}


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
# parse_daily_high
# ---------------------------------------------------------------------------


def test_parse_daily_high_returns_first_entry():
    result = parse_daily_high({"temperature_2m_max": [19.5, 17.0]})
    assert result == 19.5


def test_parse_daily_high_single_entry():
    result = parse_daily_high({"temperature_2m_max": [12.0]})
    assert result == 12.0


def test_parse_daily_high_empty_list_returns_none():
    result = parse_daily_high({"temperature_2m_max": []})
    assert result is None


def test_parse_daily_high_missing_key_returns_none():
    result = parse_daily_high({})
    assert result is None


def test_parse_daily_high_does_not_use_second_day():
    # Must return today's high (index 0), not tomorrow's
    result = parse_daily_high({"temperature_2m_max": [15.0, 20.0]})
    assert result == 15.0


# ---------------------------------------------------------------------------
# parse_daily_rainfall
# ---------------------------------------------------------------------------


def test_parse_daily_rainfall_returns_total_mm():
    result = parse_daily_rainfall({"precipitation_sum": [4.2], "precipitation_probability_max": [60]})
    assert result["total_mm"] == 4.2


def test_parse_daily_rainfall_returns_probability_percent():
    result = parse_daily_rainfall({"precipitation_sum": [4.2], "precipitation_probability_max": [60]})
    assert result["probability_percent"] == 60


def test_parse_daily_rainfall_uses_first_entry_only():
    result = parse_daily_rainfall({"precipitation_sum": [3.0, 10.0], "precipitation_probability_max": [40, 90]})
    assert result["total_mm"] == 3.0
    assert result["probability_percent"] == 40


def test_parse_daily_rainfall_missing_sum_returns_none():
    result = parse_daily_rainfall({"precipitation_probability_max": [50]})
    assert result["total_mm"] is None


def test_parse_daily_rainfall_missing_probability_returns_none():
    result = parse_daily_rainfall({"precipitation_sum": [2.0]})
    assert result["probability_percent"] is None


def test_parse_daily_rainfall_empty_dict_returns_nones():
    result = parse_daily_rainfall({})
    assert result["total_mm"] is None
    assert result["probability_percent"] is None


def test_parse_daily_rainfall_empty_lists_return_nones():
    result = parse_daily_rainfall({"precipitation_sum": [], "precipitation_probability_max": []})
    assert result["total_mm"] is None
    assert result["probability_percent"] is None


# ---------------------------------------------------------------------------
# parse_location_name
# ---------------------------------------------------------------------------


def test_parse_location_name_prefers_city():
    assert parse_location_name({"city": "London", "town": "Somewhere", "county": "Greater London"}) == "London"


def test_parse_location_name_falls_back_to_town():
    assert parse_location_name({"town": "Guildford", "county": "Surrey"}) == "Guildford"


def test_parse_location_name_falls_back_to_village():
    assert parse_location_name({"village": "Shere", "county": "Surrey"}) == "Shere"


def test_parse_location_name_falls_back_to_county():
    assert parse_location_name({"county": "Surrey"}) == "Surrey"


def test_parse_location_name_empty_dict_returns_empty_string():
    assert parse_location_name({}) == ""


def test_parse_location_name_ignores_country_and_state():
    # Should not return country/state — too broad for a weather card label
    result = parse_location_name({"country": "United Kingdom", "state": "England"})
    assert result == ""


# ---------------------------------------------------------------------------
# resolve_weather_locations
# ---------------------------------------------------------------------------


def test_resolve_office_commuter_returns_work_location():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "monday", _MOCK_SETTINGS)
    # Ryan is office on monday → commuter index 0 → commuter_1_work coords
    ryan_loc = next(loc for loc in locs if "Ryan" in loc["name"])
    assert ryan_loc["lat"] == 51.6
    assert ryan_loc["lon"] == -0.2


def test_resolve_office_commuter_label_includes_name():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "monday", _MOCK_SETTINGS)
    names = [loc["name"] for loc in locs]
    assert "Ryan's Office" in names


def test_resolve_wfh_commuter_returns_home():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "tuesday", _MOCK_SETTINGS)
    # Ryan is wfh on tuesday → home coords
    home_locs = [loc for loc in locs if loc["name"] == "Home"]
    assert len(home_locs) == 1
    assert home_locs[0]["lat"] == 51.5
    assert home_locs[0]["lon"] == -0.1


def test_resolve_off_commuter_returns_home():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "wednesday", _MOCK_SETTINGS)
    # Ryan is off on wednesday → treated as home
    home_locs = [loc for loc in locs if loc["name"] == "Home"]
    assert len(home_locs) == 1


def test_resolve_two_office_commuters_returns_two_locations():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "monday", _MOCK_SETTINGS)
    # Both Ryan and Robyn are office on monday
    assert len(locs) == 2


def test_resolve_second_office_commuter_uses_commuter2_coords():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "monday", _MOCK_SETTINGS)
    robyn_loc = next(loc for loc in locs if "Robyn" in loc["name"])
    assert robyn_loc["lat"] == 51.7
    assert robyn_loc["lon"] == -0.3


def test_resolve_second_office_commuter_label():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "monday", _MOCK_SETTINGS)
    names = [loc["name"] for loc in locs]
    assert "Robyn's Office" in names


def test_resolve_both_home_deduplicates_to_one():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "wednesday", _MOCK_SETTINGS)
    # Ryan is off (→ home), Robyn is wfh (→ home) — same coords → one entry
    assert len(locs) == 1
    assert locs[0]["name"] == "Home"


def test_resolve_one_office_one_home_returns_two_locations():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "thursday", _MOCK_SETTINGS)
    # Ryan is office, Robyn is wfh → two different locations
    assert len(locs) == 2


def test_resolve_returns_list_of_dicts_with_required_keys():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "monday", _MOCK_SETTINGS)
    for loc in locs:
        assert "name" in loc
        assert "lat" in loc
        assert "lon" in loc
        assert "geocode" in loc


def test_resolve_office_location_has_geocode_true():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "monday", _MOCK_SETTINGS)
    ryan_loc = next(loc for loc in locs if "Ryan" in loc["name"])
    assert ryan_loc["geocode"] is True


def test_resolve_home_location_has_geocode_false():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "tuesday", _MOCK_SETTINGS)
    home_loc = next(loc for loc in locs if loc["name"] == "Home")
    assert home_loc["geocode"] is False


def test_resolve_off_commuter_home_has_geocode_false():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "wednesday", _MOCK_SETTINGS)
    assert locs[0]["geocode"] is False


# ---------------------------------------------------------------------------
# Endpoint integration tests — new response shape
# ---------------------------------------------------------------------------


_CACHED_LOCATION = {
    "name": "Home",
    "current": {
        "temperature_celsius": 8.5,
        "apparent_temperature_celsius": 6.0,
        "weather_description": "Light rain",
        "wind_speed_kmh": 20.0,
        "humidity_percent": 75,
    },
    "daily_high_celsius": 12.0,
    "daily_rainfall": {"total_mm": 4.2, "probability_percent": 60},
}

_CACHED_WEATHER_DATA = {"locations": [_CACHED_LOCATION]}


@patch("routers.weather._get_now")
def test_endpoint_returns_200(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.status_code == 200
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_response_has_locations_key(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert "locations" in resp.json()
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_response_has_is_stale_key(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert "is_stale" in resp.json()
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_locations_is_a_list(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert isinstance(resp.json()["locations"], list)
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_location_entry_has_name(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["locations"][0]["name"] == "Home"
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_location_entry_has_current(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert "current" in resp.json()["locations"][0]
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_location_entry_has_daily_high(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert "daily_high_celsius" in resp.json()["locations"][0]
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_location_current_temperature(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["locations"][0]["current"]["temperature_celsius"] == 8.5
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_location_daily_high_value(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["locations"][0]["daily_high_celsius"] == 12.0
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_empty_cache_returns_empty_locations_list(mock_now):
    import routers.weather as weather_module

    weather_module._cache = None
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["locations"] == []
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_multiple_locations(mock_now):
    import routers.weather as weather_module

    weather_module._cache = {
        "locations": [
            _CACHED_LOCATION,
            {
                "name": "Ryan's Office",
                "current": {
                    "temperature_celsius": 10.0,
                    "apparent_temperature_celsius": 8.0,
                    "weather_description": "Overcast",
                    "wind_speed_kmh": 15.0,
                    "humidity_percent": 80,
                },
                "daily_high_celsius": 14.0,
                "daily_rainfall": {"total_mm": 0.0, "probability_percent": 10},
            },
        ]
    }
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert len(resp.json()["locations"]) == 2
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_location_entry_has_daily_rainfall(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert "daily_rainfall" in resp.json()["locations"][0]
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_daily_rainfall_total_mm(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["locations"][0]["daily_rainfall"]["total_mm"] == 4.2
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_daily_rainfall_probability_percent(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["locations"][0]["daily_rainfall"]["probability_percent"] == 60
    weather_module._cache = None
