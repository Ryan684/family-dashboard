"""Tests for weather backend — Open-Meteo integration."""

from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from routers.weather import (
    map_weather_code,
    map_weather_icon,
    parse_current,
    parse_daily_description,
    parse_daily_high,
    parse_daily_rainfall,
    parse_rain_windows,
    parse_location_name,
    resolve_day_offset,
    resolve_fetch_targets,
    resolve_tomorrow_weekday,
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
    # Empty, deliberately: this is what exercises fetch_warnings's own
    # no-key/no-base-url short circuit, rather than the broad `except
    # Exception` around it catching an AttributeError for the wrong reason.
    met_office_nswws_api_key = ""
    met_office_nswws_base_url = ""


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
# parse_rain_windows
# ---------------------------------------------------------------------------

_24_ZEROS = [0] * 24
_24_EIGHTIES = [80] * 24


def _hourly(probs):
    return {"precipitation_probability": probs}


def test_parse_rain_windows_consecutive_hours_form_single_window():
    probs = _24_ZEROS[:]
    probs[8] = 60
    probs[9] = 70
    probs[10] = 55
    result = parse_rain_windows(_hourly(probs))
    assert result == [{"start_hour": 8, "end_hour": 11}]


def test_parse_rain_windows_non_consecutive_form_two_windows():
    probs = _24_ZEROS[:]
    probs[8] = 60
    probs[9] = 60
    probs[14] = 65
    probs[15] = 65
    result = parse_rain_windows(_hourly(probs))
    assert result == [{"start_hour": 8, "end_hour": 10}, {"start_hour": 14, "end_hour": 16}]


def test_parse_rain_windows_below_threshold_excluded():
    probs = [49] * 24
    result = parse_rain_windows(_hourly(probs))
    assert result == []


def test_parse_rain_windows_exactly_at_threshold_included():
    probs = _24_ZEROS[:]
    probs[5] = 50
    result = parse_rain_windows(_hourly(probs))
    assert result == [{"start_hour": 5, "end_hour": 6}]


def test_parse_rain_windows_full_day_returns_single_window():
    result = parse_rain_windows(_hourly(_24_EIGHTIES))
    assert result == [{"start_hour": 0, "end_hour": 24}]


def test_parse_rain_windows_empty_data_returns_empty_list():
    assert parse_rain_windows({}) == []


def test_parse_rain_windows_no_rainy_hours_returns_empty_list():
    assert parse_rain_windows(_hourly(_24_ZEROS)) == []


def test_parse_rain_windows_window_at_end_of_day():
    probs = _24_ZEROS[:]
    probs[22] = 80
    probs[23] = 80
    result = parse_rain_windows(_hourly(probs))
    assert result == [{"start_hour": 22, "end_hour": 24}]


def test_parse_rain_windows_single_rainy_hour():
    probs = _24_ZEROS[:]
    probs[11] = 90
    result = parse_rain_windows(_hourly(probs))
    assert result == [{"start_hour": 11, "end_hour": 12}]


def test_parse_rain_windows_custom_threshold():
    probs = _24_ZEROS[:]
    probs[6] = 40  # below default 50, above custom 30
    probs[7] = 40
    result = parse_rain_windows(_hourly(probs), threshold=30)
    assert result == [{"start_hour": 6, "end_hour": 8}]


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


def test_resolve_commuter_with_no_schedule_for_weekday_defaults_to_home():
    # _TEST_SCHEDULE only covers Mon–Thu; Friday is absent from both commuters.
    # The defensive default {"mode": "off"} must kick in and map both to home.
    locs = resolve_weather_locations(_TEST_SCHEDULE, "friday", _MOCK_SETTINGS)
    assert len(locs) == 1
    assert locs[0]["name"] == "Home"


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
    "rain_windows": [{"start_hour": 8, "end_hour": 10}],
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


@patch("routers.weather._get_now")
def test_endpoint_location_entry_has_rain_windows(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert "rain_windows" in resp.json()["locations"][0]
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_rain_windows_value(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WEATHER_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["locations"][0]["rain_windows"] == [{"start_hour": 8, "end_hour": 10}]
    weather_module._cache = None


# ---------------------------------------------------------------------------
# resolve_tomorrow_weekday
# ---------------------------------------------------------------------------


def test_resolve_tomorrow_weekday_from_monday():
    assert resolve_tomorrow_weekday(datetime(2025, 1, 6)) == "tuesday"


def test_resolve_tomorrow_weekday_wraps_from_sunday():
    assert resolve_tomorrow_weekday(datetime(2025, 1, 5)) == "monday"


def test_resolve_tomorrow_weekday_is_lowercase():
    assert resolve_tomorrow_weekday(datetime(2025, 1, 1)).islower()


def test_resolve_tomorrow_weekday_crosses_month_end():
    assert resolve_tomorrow_weekday(datetime(2025, 1, 31)) == "saturday"


def test_resolve_weather_locations_for_a_weekend_day_defaults_to_home():
    locs = resolve_weather_locations(_TEST_SCHEDULE, "saturday", _MOCK_SETTINGS)
    assert [loc["name"] for loc in locs] == ["Home"]


# ---------------------------------------------------------------------------
# resolve_fetch_targets
# ---------------------------------------------------------------------------


def _loc(name, lat, lon, geocode=False):
    return {"name": name, "lat": lat, "lon": lon, "geocode": geocode}


def test_resolve_fetch_targets_identical_sets_are_not_duplicated():
    today = [_loc("Home", 51.5, -0.1)]
    tomorrow = [_loc("Home", 51.5, -0.1)]
    assert len(resolve_fetch_targets(today, tomorrow)) == 1


def test_resolve_fetch_targets_adds_a_tomorrow_only_location():
    today = [_loc("Home", 51.5, -0.1)]
    tomorrow = [_loc("Home", 51.5, -0.1), _loc("Ryan's Office", 51.6, -0.2, True)]
    assert len(resolve_fetch_targets(today, tomorrow)) == 2


def test_resolve_fetch_targets_preserves_today_first_ordering():
    today = [_loc("Home", 51.5, -0.1)]
    tomorrow = [_loc("Ryan's Office", 51.6, -0.2, True)]
    targets = resolve_fetch_targets(today, tomorrow)
    assert [(t["lat"], t["lon"]) for t in targets] == [(51.5, -0.1), (51.6, -0.2)]


def test_resolve_fetch_targets_geocode_true_if_either_day_wants_it():
    today = [_loc("Home", 51.6, -0.2, False)]
    tomorrow = [_loc("Ryan's Office", 51.6, -0.2, True)]
    targets = resolve_fetch_targets(today, tomorrow)
    assert targets[0]["geocode"] is True


def test_resolve_fetch_targets_geocode_false_when_neither_day_wants_it():
    today = [_loc("Home", 51.5, -0.1, False)]
    tomorrow = [_loc("Home", 51.5, -0.1, False)]
    assert resolve_fetch_targets(today, tomorrow)[0]["geocode"] is False


def test_resolve_fetch_targets_empty_inputs_return_empty():
    assert resolve_fetch_targets([], []) == []


# ---------------------------------------------------------------------------
# parse_daily_high / parse_daily_rainfall — day_index
# ---------------------------------------------------------------------------


def test_parse_daily_high_reads_tomorrow():
    daily = {"temperature_2m_max": [18.1, 21.4]}
    assert parse_daily_high(daily, 1) == 21.4


def test_parse_daily_high_beyond_end_is_none():
    assert parse_daily_high({"temperature_2m_max": [18.1]}, 1) is None


def test_parse_daily_high_defaults_to_today():
    assert parse_daily_high({"temperature_2m_max": [18.1, 21.4]}) == 18.1


def test_parse_daily_rainfall_reads_tomorrow():
    daily = {
        "precipitation_sum": [0.0, 3.1],
        "precipitation_probability_max": [10, 70],
    }
    assert parse_daily_rainfall(daily, 1) == {
        "total_mm": 3.1,
        "probability_percent": 70,
    }


def test_parse_daily_rainfall_handles_asymmetric_list_lengths():
    daily = {
        "precipitation_sum": [0.0, 3.1],
        "precipitation_probability_max": [10],
    }
    result = parse_daily_rainfall(daily, 1)
    assert result["total_mm"] == 3.1
    assert result["probability_percent"] is None


def test_parse_daily_rainfall_beyond_end_is_none():
    daily = {"precipitation_sum": [0.0], "precipitation_probability_max": [10]}
    assert parse_daily_rainfall(daily, 1) == {
        "total_mm": None,
        "probability_percent": None,
    }


# ---------------------------------------------------------------------------
# parse_daily_description
# ---------------------------------------------------------------------------


def test_parse_daily_description_reads_tomorrow():
    assert parse_daily_description({"weather_code": [0, 61]}, 1) == "Light rain"


def test_parse_daily_description_defaults_to_today():
    assert parse_daily_description({"weather_code": [0, 61]}) == "Clear sky"


def test_parse_daily_description_missing_list_is_none():
    assert parse_daily_description({}) is None


def test_parse_daily_description_beyond_end_is_none():
    assert parse_daily_description({"weather_code": [0]}, 1) is None


def test_parse_daily_description_unknown_code_is_unknown():
    assert parse_daily_description({"weather_code": [999]}) == "Unknown"


# ---------------------------------------------------------------------------
# map_weather_icon
# ---------------------------------------------------------------------------


def test_map_weather_icon_clear_sky_is_sun():
    assert map_weather_icon(0) == "sun"


def test_map_weather_icon_mainly_clear_is_sun():
    assert map_weather_icon(1) == "sun"


def test_map_weather_icon_light_rain_is_rain():
    assert map_weather_icon(61) == "rain"


def test_map_weather_icon_showers_are_rain():
    assert map_weather_icon(80) == "rain"


def test_map_weather_icon_snow_is_rain():
    assert map_weather_icon(71) == "rain"


def test_map_weather_icon_thunderstorm_is_rain():
    assert map_weather_icon(95) == "rain"


def test_map_weather_icon_overcast_is_cloud():
    assert map_weather_icon(3) == "cloud"


def test_map_weather_icon_fog_is_cloud():
    assert map_weather_icon(45) == "cloud"


def test_map_weather_icon_unknown_code_is_cloud():
    assert map_weather_icon(999) == "cloud"


# ---------------------------------------------------------------------------
# resolve_day_offset
# ---------------------------------------------------------------------------


def _times(*counts):
    """Build an hourly time list: counts[i] entries for consecutive dates."""
    out = []
    for day, count in enumerate(counts, start=1):
        out.extend(f"2026-03-{day:02d}T{h:02d}:00" for h in range(count))
    return out


def test_resolve_day_offset_today_is_zero():
    assert resolve_day_offset({"time": _times(24, 24)}, 0) == 0


def test_resolve_day_offset_normal_day_is_24():
    assert resolve_day_offset({"time": _times(24, 24)}, 1) == 24


def test_resolve_day_offset_clocks_back_day_is_25():
    assert resolve_day_offset({"time": _times(25, 24)}, 1) == 25


def test_resolve_day_offset_clocks_forward_day_is_23():
    assert resolve_day_offset({"time": _times(23, 24)}, 1) == 23


def test_resolve_day_offset_without_times_falls_back_to_whole_days():
    assert resolve_day_offset({}, 1) == 24


def test_resolve_day_offset_missing_day_falls_back_to_whole_days():
    assert resolve_day_offset({"time": _times(24)}, 1) == 24


# ---------------------------------------------------------------------------
# parse_rain_windows — day_index
# ---------------------------------------------------------------------------


def _hourly48(probs):
    return {"precipitation_probability": probs, "time": _times(24, 24)}


def test_parse_rain_windows_tomorrow_reported_in_local_hours():
    probs = [0] * 48
    for h in range(32, 36):
        probs[h] = 80
    result = parse_rain_windows(_hourly48(probs), 50, 1)
    assert result == [{"start_hour": 8, "end_hour": 12}]


def test_parse_rain_windows_tomorrow_does_not_run_past_the_day():
    probs = [0] * 48
    for h in range(44, 48):
        probs[h] = 80
    result = parse_rain_windows(_hourly48(probs), 50, 1)
    assert result == [{"start_hour": 20, "end_hour": 24}]


def test_parse_rain_windows_tomorrow_ignores_todays_rain():
    probs = [0] * 48
    for h in range(8, 12):
        probs[h] = 80
    assert parse_rain_windows(_hourly48(probs), 50, 1) == []


def test_parse_rain_windows_today_ignores_tomorrows_rain():
    probs = [0] * 48
    for h in range(32, 36):
        probs[h] = 80
    assert parse_rain_windows(_hourly48(probs), 50, 0) == []


def test_parse_rain_windows_tomorrow_when_only_today_fetched():
    assert parse_rain_windows(_hourly(_24_EIGHTIES), 50, 1) == []


def test_parse_rain_windows_tomorrow_respects_a_dst_offset():
    # 25-hour local day: tomorrow's hour 0 is absolute index 25, not 24.
    probs = [0] * 49
    probs[25] = 80
    hourly = {"precipitation_probability": probs, "time": _times(25, 24)}
    assert parse_rain_windows(hourly, 50, 1) == [{"start_hour": 0, "end_hour": 1}]


# ---------------------------------------------------------------------------
# Endpoint — tomorrow block
# ---------------------------------------------------------------------------


_CACHED_TOMORROW_LOCATION = {
    "name": "Home",
    "icon": "rain",
    "daily_high_celsius": 17.4,
    "weather_description": "Light rain",
    "daily_rainfall": {"total_mm": 3.1, "probability_percent": 70},
    "rain_windows": [{"start_hour": 14, "end_hour": 17}],
}

_CACHED_WITH_TOMORROW = {
    "locations": [_CACHED_LOCATION],
    "tomorrow": {
        "weekday": "Wednesday",
        "locations": [_CACHED_TOMORROW_LOCATION],
    },
}


@patch("routers.weather._get_now")
def test_endpoint_returns_tomorrow_block(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WITH_TOMORROW
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["tomorrow"]["weekday"] == "Wednesday"
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_tomorrow_has_locations(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WITH_TOMORROW
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["tomorrow"]["locations"][0]["name"] == "Home"
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_tomorrow_entries_have_no_current_block(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WITH_TOMORROW
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    for entry in resp.json()["tomorrow"]["locations"]:
        assert "current" not in entry
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_tomorrow_entry_has_a_daily_high(mock_now):
    import routers.weather as weather_module

    weather_module._cache = _CACHED_WITH_TOMORROW
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert resp.json()["tomorrow"]["locations"][0]["daily_high_celsius"] == 17.4
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_endpoint_empty_cache_omits_tomorrow(mock_now):
    import routers.weather as weather_module

    weather_module._cache = None
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    resp = client.get("/api/weather")
    assert "tomorrow" not in resp.json()


@patch("routers.weather._get_now")
def test_endpoint_empty_cache_still_returns_empty_locations(mock_now):
    import routers.weather as weather_module

    weather_module._cache = None
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    assert client.get("/api/weather").json()["locations"] == []


# ---------------------------------------------------------------------------
# fetch_weather_data
# ---------------------------------------------------------------------------


def _open_meteo_response(
    current_code=61, daily_codes=(3, 61), highs=(12.0, 17.4), probs=None
):
    """A two-day Open-Meteo forecast response with 48 aligned hourly entries."""
    if probs is None:
        probs = [0] * 48
    return {
        "current": {
            "temperature_2m": 8.5,
            "apparent_temperature": 6.0,
            "weather_code": current_code,
            "wind_speed_10m": 20.0,
            "relative_humidity_2m": 75,
        },
        "daily": {
            "temperature_2m_max": list(highs),
            "precipitation_sum": [4.2, 3.1],
            "precipitation_probability_max": [60, 70],
            "weather_code": list(daily_codes),
        },
        "hourly": {"precipitation_probability": probs, "time": _times(24, 24)},
    }


_UNSET = object()


def _patched_fetch(schedule=None, response=_UNSET, now=datetime(2025, 1, 6, 7, 30)):
    """Patch weather's schedule, clock and outbound calls for fetch_weather_data.

    `response` uses a sentinel rather than None so that an empty dict — the
    degenerate-payload case — is passed through instead of being replaced.
    """
    from unittest.mock import AsyncMock

    return (
        patch("routers.weather.load_schedule", return_value=schedule or _TEST_SCHEDULE),
        patch("routers.weather._get_now", return_value=now),
        patch("routers.weather.settings", _MOCK_SETTINGS),
        patch(
            "routers.weather.fetch_weather",
            new_callable=AsyncMock,
            return_value=(
                _open_meteo_response() if response is _UNSET else response
            ),
        ),
        patch(
            "routers.weather.fetch_location_name",
            new_callable=AsyncMock,
            return_value="Guildford",
        ),
    )


async def _run_fetch(**kwargs):
    from routers.weather import fetch_weather_data

    patches = _patched_fetch(**kwargs)
    for p in patches:
        p.start()
    try:
        return await fetch_weather_data()
    finally:
        for p in patches:
            p.stop()


async def test_fetch_weather_data_returns_today_and_tomorrow():
    result = await _run_fetch()
    assert "locations" in result and "tomorrow" in result


async def test_fetch_weather_data_tomorrow_weekday_is_capitalised():
    # Monday 2025-01-06 → tomorrow is Tuesday
    result = await _run_fetch()
    assert result["tomorrow"]["weekday"] == "Tuesday"


async def test_fetch_weather_data_today_entry_has_current_conditions():
    result = await _run_fetch()
    assert result["locations"][0]["current"]["temperature_celsius"] == 8.5


async def test_fetch_weather_data_today_icon_comes_from_current_code():
    result = await _run_fetch(response=_open_meteo_response(current_code=61))
    assert result["locations"][0]["icon"] == "rain"


async def test_fetch_weather_data_today_icon_reflects_a_clear_sky():
    result = await _run_fetch(response=_open_meteo_response(current_code=0))
    assert result["locations"][0]["icon"] == "sun"


async def test_fetch_weather_data_tomorrow_entry_has_no_current_block():
    result = await _run_fetch()
    for entry in result["tomorrow"]["locations"]:
        assert "current" not in entry


async def test_fetch_weather_data_tomorrow_uses_the_second_daily_high():
    result = await _run_fetch()
    assert result["tomorrow"]["locations"][0]["daily_high_celsius"] == 17.4


async def test_fetch_weather_data_today_uses_the_first_daily_high():
    result = await _run_fetch()
    assert result["locations"][0]["daily_high_celsius"] == 12.0


async def test_fetch_weather_data_tomorrow_description_from_daily_code():
    result = await _run_fetch(response=_open_meteo_response(daily_codes=(3, 61)))
    assert result["tomorrow"]["locations"][0]["weather_description"] == "Light rain"


async def test_fetch_weather_data_tomorrow_icon_from_daily_code():
    result = await _run_fetch(response=_open_meteo_response(daily_codes=(3, 0)))
    assert result["tomorrow"]["locations"][0]["icon"] == "sun"


async def test_fetch_weather_data_tomorrow_rain_windows_are_local_hours():
    probs = [0] * 48
    for h in range(32, 36):
        probs[h] = 80
    result = await _run_fetch(response=_open_meteo_response(probs=probs))
    assert result["tomorrow"]["locations"][0]["rain_windows"] == [
        {"start_hour": 8, "end_hour": 12}
    ]


async def test_fetch_weather_data_office_location_is_geocoded():
    # Monday: both commuters are in the office, so both names are geocoded
    result = await _run_fetch()
    assert "Guildford" in [loc["name"] for loc in result["locations"]]


async def _fetch_call_count(now):
    """Run fetch_weather_data and report how many upstream forecasts it fetched."""
    from unittest.mock import AsyncMock

    from routers.weather import fetch_weather_data

    fetch_mock = AsyncMock(return_value=_open_meteo_response())
    with (
        patch("routers.weather.load_schedule", return_value=_TEST_SCHEDULE),
        patch("routers.weather._get_now", return_value=now),
        patch("routers.weather.settings", _MOCK_SETTINGS),
        patch("routers.weather.fetch_weather", fetch_mock),
        patch(
            "routers.weather.fetch_location_name",
            new_callable=AsyncMock,
            return_value="Guildford",
        ),
    ):
        await fetch_weather_data()
    return fetch_mock.await_count


async def test_fetch_weather_data_unions_both_days_coordinates():
    # Monday: both in the office → 2 coords. Tuesday: Ryan wfh, Robyn off → home.
    # The union is 3 unique coordinates, so 3 calls rather than 4.
    assert await _fetch_call_count(datetime(2025, 1, 6, 7, 30)) == 3


async def test_fetch_weather_data_costs_nothing_extra_when_days_match():
    # Wednesday: Ryan off, Robyn wfh → home only. Thursday: Ryan office, Robyn wfh.
    # Today needs 1 coordinate, tomorrow adds the office → 2, not 3.
    assert await _fetch_call_count(datetime(2025, 1, 8, 7, 30)) == 2


async def test_fetch_weather_data_deduplicates_both_commuters_at_home():
    # Wednesday today: Ryan off, Robyn wfh — both resolve to Home, shown once.
    result = await _run_fetch(now=datetime(2025, 1, 8, 7, 30))
    assert [loc["name"] for loc in result["locations"]] == ["Home"]


async def test_fetch_weather_data_tomorrow_follows_tomorrows_modes():
    # Wednesday today (both home); Thursday tomorrow: Ryan office, Robyn wfh.
    result = await _run_fetch(now=datetime(2025, 1, 8, 7, 30))
    assert len(result["tomorrow"]["locations"]) == 2


# ---------------------------------------------------------------------------
# Endpoint — /api/weather/warnings
# ---------------------------------------------------------------------------


_CACHED_WARNING = {
    "id": "w1",
    "level": "AMBER",
    "weather_type": "rain",
    "headline": "Heavy rain may cause flooding",
    "issued": "2026-08-20T09:00:00Z",
    "valid_from": "2026-08-21T06:00:00Z",
    "valid_to": "2026-08-21T18:00:00Z",
    "locations": ["Home"],
}


def test_warnings_endpoint_serves_the_cached_warnings():
    import routers.weather as weather_module

    weather_module._cache = {"locations": [], "warnings": [_CACHED_WARNING]}
    resp = client.get("/api/weather/warnings")
    assert resp.json()["warnings"][0]["headline"] == "Heavy rain may cause flooding"
    weather_module._cache = None


def test_warnings_endpoint_empty_cache_returns_empty_list():
    import routers.weather as weather_module

    weather_module._cache = None
    assert client.get("/api/weather/warnings").json() == {"warnings": []}


def test_warnings_endpoint_cache_without_warnings_key_returns_empty_list():
    # A cache written before this feature shipped, e.g. mid rolling deploy.
    import routers.weather as weather_module

    weather_module._cache = {"locations": [_CACHED_LOCATION]}
    assert client.get("/api/weather/warnings").json() == {"warnings": []}
    weather_module._cache = None


def test_warnings_endpoint_returns_yellow_warnings():
    # The API stays truthful about what the Met Office issued; the decision to
    # hide yellow lives in the banner.
    import routers.weather as weather_module

    yellow = {**_CACHED_WARNING, "level": "YELLOW"}
    weather_module._cache = {"locations": [], "warnings": [yellow]}
    resp = client.get("/api/weather/warnings")
    assert resp.json()["warnings"][0]["level"] == "YELLOW"
    weather_module._cache = None


def test_warnings_endpoint_has_no_is_stale_flag():
    import routers.weather as weather_module

    weather_module._cache = {"locations": [], "warnings": []}
    assert "is_stale" not in client.get("/api/weather/warnings").json()
    weather_module._cache = None


@patch("routers.weather._get_now")
def test_weather_endpoint_still_carries_warnings_inline(mock_now):
    import routers.weather as weather_module

    weather_module._cache = {"locations": [], "warnings": [_CACHED_WARNING]}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)
    assert len(client.get("/api/weather").json()["warnings"]) == 1
    weather_module._cache = None


async def test_fetch_weather_data_without_a_key_returns_no_warnings():
    result = await _run_fetch()
    assert result["warnings"] == []


async def test_fetch_weather_data_survives_a_warnings_failure():
    from unittest.mock import AsyncMock

    from routers.weather import fetch_weather_data

    patches = _patched_fetch()
    for p in patches:
        p.start()
    boom = patch(
        "routers.weather.fetch_warnings",
        new_callable=AsyncMock,
        side_effect=RuntimeError("NSWWS down"),
    )
    boom.start()
    try:
        result = await fetch_weather_data()
    finally:
        boom.stop()
        for p in patches:
            p.stop()
    # The forecast is what people rely on each morning; it must survive.
    assert result["warnings"] == []
    assert len(result["locations"]) > 0


# ---------------------------------------------------------------------------
# fetch_weather_data — today and tomorrow must not be confused
# ---------------------------------------------------------------------------


async def test_fetch_weather_data_today_rainfall_is_todays():
    # The fixture carries 4.2mm/60% today and 3.1mm/70% tomorrow. Reading the
    # wrong index here would put tomorrow's rain on today's card.
    result = await _run_fetch()
    assert result["locations"][0]["daily_rainfall"] == {
        "total_mm": 4.2,
        "probability_percent": 60,
    }


async def test_fetch_weather_data_tomorrow_rainfall_is_tomorrows():
    result = await _run_fetch()
    assert result["tomorrow"]["locations"][0]["daily_rainfall"] == {
        "total_mm": 3.1,
        "probability_percent": 70,
    }


async def test_fetch_weather_data_today_rain_windows_are_todays():
    probs = [0] * 48
    for h in range(8, 12):
        probs[h] = 80
    result = await _run_fetch(response=_open_meteo_response(probs=probs))
    assert result["locations"][0]["rain_windows"] == [
        {"start_hour": 8, "end_hour": 12}
    ]


async def test_fetch_weather_data_today_ignores_tomorrows_rain():
    probs = [0] * 48
    for h in range(32, 36):
        probs[h] = 80
    result = await _run_fetch(response=_open_meteo_response(probs=probs))
    assert result["locations"][0]["rain_windows"] == []


async def test_fetch_weather_data_today_entry_carries_every_field():
    result = await _run_fetch()
    assert set(result["locations"][0]) == {
        "name",
        "icon",
        "current",
        "daily_high_celsius",
        "daily_rainfall",
        "rain_windows",
    }


async def test_fetch_weather_data_tomorrow_entry_carries_every_field():
    result = await _run_fetch()
    assert set(result["tomorrow"]["locations"][0]) == {
        "name",
        "icon",
        "weather_description",
        "daily_high_celsius",
        "daily_rainfall",
        "rain_windows",
    }


async def test_fetch_weather_data_tomorrow_icon_falls_back_when_only_one_code():
    # A one-day daily block must not index past the end reaching for tomorrow.
    response = _open_meteo_response()
    response["daily"]["weather_code"] = [3]
    result = await _run_fetch(response=response)
    assert result["tomorrow"]["locations"][0]["icon"] == "cloud"


async def test_fetch_weather_data_tomorrow_high_is_none_when_only_one_day():
    response = _open_meteo_response()
    response["daily"]["temperature_2m_max"] = [12.0]
    result = await _run_fetch(response=response)
    assert result["tomorrow"]["locations"][0]["daily_high_celsius"] is None


def test_resolve_day_offset_defaults_to_today():
    assert resolve_day_offset({"time": _times(24, 24)}) == 0


async def test_fetch_weather_data_survives_a_response_with_no_blocks():
    # Every field here is read with a .get fallback; this is the test that the
    # fallbacks actually hold rather than raising inside the poll loop.
    result = await _run_fetch(response={})
    assert result["locations"][0]["daily_high_celsius"] is None
    assert result["locations"][0]["rain_windows"] == []
    assert result["tomorrow"]["locations"][0]["weather_description"] is None


async def test_fetch_weather_data_missing_current_block_gives_a_sun_glyph():
    # map_weather_icon's input defaults to code 0 — clear sky — when the current
    # block carries no weather_code at all.
    result = await _run_fetch(response={})
    assert result["locations"][0]["icon"] == "sun"


async def test_fetch_weather_data_missing_daily_block_gives_a_cloud_glyph():
    result = await _run_fetch(response={})
    assert result["tomorrow"]["locations"][0]["icon"] == "cloud"


# ---------------------------------------------------------------------------
# fetch_weather — the request contract with Open-Meteo
# ---------------------------------------------------------------------------


def _make_forecast_client():
    from unittest.mock import AsyncMock, MagicMock

    response = MagicMock()
    response.json.return_value = _open_meteo_response()
    response.raise_for_status = MagicMock()
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    return client


async def test_fetch_weather_requests_two_days():
    # Tomorrow's forecast rides on the same request as today's; dropping to one
    # day would silently empty the tomorrow column.
    from routers.weather import fetch_weather

    client = _make_forecast_client()
    await fetch_weather(client, 51.5, -0.1)
    assert client.get.call_args[1]["params"]["forecast_days"] == 2


async def test_fetch_weather_requests_the_daily_weather_code():
    # Tomorrow's description and glyph both come from the daily code.
    from routers.weather import fetch_weather

    client = _make_forecast_client()
    await fetch_weather(client, 51.5, -0.1)
    assert "weather_code" in client.get.call_args[1]["params"]["daily"]


async def test_fetch_weather_requests_hourly_precipitation_probability():
    from routers.weather import fetch_weather

    client = _make_forecast_client()
    await fetch_weather(client, 51.5, -0.1)
    assert client.get.call_args[1]["params"]["hourly"] == "precipitation_probability"


async def test_fetch_weather_pins_the_london_timezone():
    # Local-day alignment is what makes the DST-aware day offsets work.
    from routers.weather import fetch_weather

    client = _make_forecast_client()
    await fetch_weather(client, 51.5, -0.1)
    assert client.get.call_args[1]["params"]["timezone"] == "Europe/London"


async def test_fetch_weather_passes_the_coordinates():
    from routers.weather import fetch_weather

    client = _make_forecast_client()
    await fetch_weather(client, 51.5, -0.1)
    params = client.get.call_args[1]["params"]
    assert (params["latitude"], params["longitude"]) == (51.5, -0.1)
