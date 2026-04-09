"""Tests for travel backend — Google Maps Routes API integration."""

import re
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from routers.travel import (
    _build_all_points,
    _build_route_option,
    _collect_instructions,
    _collect_points,
    _normalize_google_response,
    _normalize_here_response,
    _parse_duration,
    calculate_bounding_box,
    classify_delay,
    expand_bounding_box,
    extract_road_names,
    fetch_incidents,
    format_route_description,
    is_within_poll_window,
    parse_incidents,
)

client = TestClient(app)


# ---------------------------------------------------------------------------
# classify_delay
# ---------------------------------------------------------------------------


def test_classify_delay_green_below_10_percent():
    assert classify_delay(99, 1000) == "green"


def test_classify_delay_green_zero_delay():
    assert classify_delay(0, 1000) == "green"


def test_classify_delay_amber_at_exactly_10_percent():
    assert classify_delay(100, 1000) == "amber"


def test_classify_delay_amber_between_10_and_25_percent():
    assert classify_delay(200, 1000) == "amber"


def test_classify_delay_amber_at_exactly_25_percent():
    assert classify_delay(250, 1000) == "amber"


def test_classify_delay_red_above_25_percent():
    assert classify_delay(251, 1000) == "red"


def test_classify_delay_red_large_delay():
    assert classify_delay(600, 1000) == "red"


def test_classify_delay_green_when_no_traffic_time_zero():
    # Guard against division by zero — treat as no delay
    assert classify_delay(0, 0) == "green"


# ---------------------------------------------------------------------------
# extract_road_names
# ---------------------------------------------------------------------------


def test_extract_road_names_returns_motorways_and_a_roads():
    instructions = [
        {"roadName": "High Street"},
        {"roadName": "A3"},
        {"roadName": "Some Lane"},
        {"roadName": "M25"},
    ]
    assert extract_road_names(instructions) == ["A3", "M25"]


def test_extract_road_names_excludes_minor_roads():
    instructions = [
        {"roadName": "Local Street"},
        {"roadName": "B1234"},
        {"roadName": "Some Road"},
    ]
    assert extract_road_names(instructions) == []


def test_extract_road_names_limits_to_three():
    instructions = [
        {"roadName": "A3"},
        {"roadName": "M25"},
        {"roadName": "A316"},
        {"roadName": "M4"},
    ]
    result = extract_road_names(instructions)
    assert result == ["A3", "M25", "A316"]


def test_extract_road_names_deduplicates():
    instructions = [
        {"roadName": "A3"},
        {"roadName": "A3"},
        {"roadName": "M25"},
    ]
    assert extract_road_names(instructions) == ["A3", "M25"]


def test_extract_road_names_handles_missing_road_name():
    instructions = [
        {},
        {"roadName": "A3"},
    ]
    assert extract_road_names(instructions) == ["A3"]


# ---------------------------------------------------------------------------
# format_route_description
# ---------------------------------------------------------------------------


def test_format_description_single_road():
    assert format_route_description(["A3"]) == "via A3"


def test_format_description_two_roads():
    assert format_route_description(["A3", "M25"]) == "via A3 and M25"


def test_format_description_three_roads():
    assert format_route_description(["A3", "M25", "A316"]) == "via A3, M25 and A316"


def test_format_description_empty():
    assert format_route_description([]) == ""


# ---------------------------------------------------------------------------
# calculate_bounding_box
# ---------------------------------------------------------------------------


def test_calculate_bounding_box():
    points = [
        {"latitude": 51.5, "longitude": -0.1},
        {"latitude": 51.4, "longitude": -0.3},
        {"latitude": 51.6, "longitude": 0.1},
    ]
    bbox = calculate_bounding_box(points)
    assert bbox["min_lat"] == pytest.approx(51.4)
    assert bbox["max_lat"] == pytest.approx(51.6)
    assert bbox["min_lon"] == pytest.approx(-0.3)
    assert bbox["max_lon"] == pytest.approx(0.1)


def test_calculate_bounding_box_single_point():
    points = [{"latitude": 51.5, "longitude": -0.1}]
    bbox = calculate_bounding_box(points)
    assert bbox["min_lat"] == pytest.approx(51.5)
    assert bbox["max_lat"] == pytest.approx(51.5)


# ---------------------------------------------------------------------------
# expand_bounding_box
# ---------------------------------------------------------------------------


def test_expand_bounding_box_default_degrees():
    bbox = {"min_lat": 51.4, "max_lat": 51.6, "min_lon": -0.3, "max_lon": 0.1}
    expanded = expand_bounding_box(bbox)
    assert expanded["min_lat"] == pytest.approx(51.38)
    assert expanded["max_lat"] == pytest.approx(51.62)
    assert expanded["min_lon"] == pytest.approx(-0.32)
    assert expanded["max_lon"] == pytest.approx(0.12)


def test_expand_bounding_box_custom_degrees():
    bbox = {"min_lat": 51.5, "max_lat": 51.5, "min_lon": 0.0, "max_lon": 0.0}
    expanded = expand_bounding_box(bbox, degrees=0.05)
    assert expanded["min_lat"] == pytest.approx(51.45)
    assert expanded["max_lat"] == pytest.approx(51.55)


# ---------------------------------------------------------------------------
# is_within_poll_window
# ---------------------------------------------------------------------------


def test_is_within_poll_window_returns_true_inside():
    now = datetime(2025, 1, 1, 7, 0, 0)
    assert is_within_poll_window(now, time(6, 30), time(9, 30)) is True


def test_is_within_poll_window_returns_false_before():
    now = datetime(2025, 1, 1, 6, 0, 0)
    assert is_within_poll_window(now, time(6, 30), time(9, 30)) is False


def test_is_within_poll_window_returns_false_after():
    now = datetime(2025, 1, 1, 10, 0, 0)
    assert is_within_poll_window(now, time(6, 30), time(9, 30)) is False


def test_is_within_poll_window_at_start_boundary():
    now = datetime(2025, 1, 1, 6, 30, 0)
    assert is_within_poll_window(now, time(6, 30), time(9, 30)) is True


def test_is_within_poll_window_at_end_boundary():
    now = datetime(2025, 1, 1, 9, 30, 0)
    assert is_within_poll_window(now, time(6, 30), time(9, 30)) is True


# ---------------------------------------------------------------------------
# parse_incidents
# ---------------------------------------------------------------------------


def test_parse_incidents_excludes_minor():
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 1,
                "iconCategory": "ACCIDENT",
                "events": [{"description": "Minor congestion"}],
                "roadNumbers": ["A3"],
            }
        }
    ]
    assert parse_incidents(raw) == []


def test_parse_incidents_includes_moderate():
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 2,
                "iconCategory": "ACCIDENT",
                "events": [{"description": "Multi-vehicle accident"}],
                "roadNumbers": ["M25"],
            }
        }
    ]
    result = parse_incidents(raw)
    assert len(result) == 1
    assert result[0]["type"] == "ACCIDENT"
    assert result[0]["description"] == "Multi-vehicle accident"
    assert result[0]["road"] == "M25"


def test_parse_incidents_includes_major():
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 3,
                "iconCategory": "ROAD_CLOSED",
                "events": [{"description": "Road closure"}],
                "roadNumbers": ["M4"],
            }
        }
    ]
    result = parse_incidents(raw)
    assert len(result) == 1
    assert result[0]["type"] == "ROAD_CLOSED"


def test_parse_incidents_excludes_unknown_magnitude():
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 0,
                "iconCategory": "ACCIDENT",
                "events": [],
                "roadNumbers": [],
            }
        }
    ]
    assert parse_incidents(raw) == []


def test_parse_incidents_handles_empty_events():
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 2,
                "iconCategory": "CONGESTION",
                "events": [],
                "roadNumbers": ["A316"],
            }
        }
    ]
    result = parse_incidents(raw)
    assert result[0]["description"] == ""
    assert result[0]["road"] == "A316"


def test_parse_incidents_road_falls_back_to_from_field():
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 2,
                "iconCategory": "CONGESTION",
                "events": [],
                "roadNumbers": [],
                "from": "Junction 5",
            }
        }
    ]
    result = parse_incidents(raw)
    assert result[0]["road"] == "Junction 5"


def test_parse_incidents_multiple_skips_minor_between_major():
    # Ensures `continue` (not `break`) is used when skipping minor incidents
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 1,
                "iconCategory": "CONGESTION",
                "events": [],
                "roadNumbers": ["A3"],
            }
        },
        {
            "properties": {
                "magnitudeOfDelay": 3,
                "iconCategory": "ACCIDENT",
                "events": [{"description": "Crash"}],
                "roadNumbers": ["M25"],
            }
        },
    ]
    result = parse_incidents(raw)
    assert len(result) == 1
    assert result[0]["road"] == "M25"


def test_parse_incidents_missing_magnitude_defaults_to_zero():
    # Ensures default for magnitudeOfDelay is 0 (excluded), not a number >=2
    raw = [
        {
            "properties": {
                "iconCategory": "UNKNOWN",
                "events": [],
                "roadNumbers": [],
            }
        }
    ]
    assert parse_incidents(raw) == []


# ---------------------------------------------------------------------------
# Private helper unit tests
# ---------------------------------------------------------------------------


def test_collect_points_extracts_from_legs():
    route = {
        "legs": [
            {"points": [{"latitude": 51.5, "longitude": -0.1}]},
            {"points": [{"latitude": 51.6, "longitude": -0.2}]},
        ]
    }
    pts = _collect_points(route)
    assert len(pts) == 2
    assert pts[0]["latitude"] == 51.5


def test_collect_points_missing_legs_returns_empty():
    # Ensures default [] is used when "legs" key absent
    assert _collect_points({}) == []


def test_collect_points_missing_points_in_leg():
    route = {"legs": [{}]}
    assert _collect_points(route) == []


def test_collect_instructions_extracts_from_legs():
    route = {
        "legs": [
            {
                "guidance": {
                    "instructions": [{"roadName": "A3"}, {"roadName": "M25"}]
                }
            }
        ]
    }
    insts = _collect_instructions(route)
    assert len(insts) == 2
    assert insts[0]["roadName"] == "A3"


def test_collect_instructions_missing_legs_returns_empty():
    assert _collect_instructions({}) == []


def test_collect_instructions_missing_guidance_returns_empty():
    route = {"legs": [{}]}
    assert _collect_instructions(route) == []


def test_build_route_option_uses_traffic_delay_seconds():
    route = {
        "summary": {
            "lengthInMeters": 10000,
            "travelTimeInSeconds": 600,
            "trafficDelayInSeconds": 120,
            "noTrafficTravelTimeInSeconds": 500,
            "trafficModelId": "x",
        },
        "legs": [],
    }
    result = _build_route_option(route)
    assert result["delay_seconds"] == 120


def test_build_route_option_falls_back_to_computed_delay():
    # When trafficDelayInSeconds is absent, fallback is travel_time - no_traffic_time
    route = {
        "summary": {
            "lengthInMeters": 10000,
            "travelTimeInSeconds": 600,
            "noTrafficTravelTimeInSeconds": 500,
        },
        "legs": [],
    }
    result = _build_route_option(route)
    assert result["delay_seconds"] == 100  # 600 - 500


def test_build_route_option_fallback_delay_never_negative():
    route = {
        "summary": {
            "lengthInMeters": 10000,
            "travelTimeInSeconds": 490,
            "noTrafficTravelTimeInSeconds": 500,
        },
        "legs": [],
    }
    result = _build_route_option(route)
    assert result["delay_seconds"] == 0


def test_build_route_option_fields():
    route = {
        "summary": {
            "lengthInMeters": 25000,
            "travelTimeInSeconds": 1800,
            "trafficDelayInSeconds": 90,
            "noTrafficTravelTimeInSeconds": 1650,
        },
        "legs": [
            {
                "points": [{"latitude": 51.5, "longitude": -0.1}],
                "guidance": {"instructions": [{"roadName": "A3"}]},
            }
        ],
    }
    result = _build_route_option(route)
    assert result["travel_time_seconds"] == 1800
    assert result["distance_meters"] == 25000
    assert result["description"] == "via A3"
    assert result["delay_colour"] == "green"


def test_build_route_option_includes_encoded_polyline():
    route = {
        "summary": {
            "lengthInMeters": 25000,
            "travelTimeInSeconds": 1800,
            "trafficDelayInSeconds": 90,
            "noTrafficTravelTimeInSeconds": 1650,
        },
        "encoded_polyline": "xyz789",
        "legs": [],
    }
    result = _build_route_option(route)
    assert result["encoded_polyline"] == "xyz789"


def test_build_route_option_encoded_polyline_defaults_empty():
    route = {
        "summary": {
            "lengthInMeters": 25000,
            "travelTimeInSeconds": 1800,
            "trafficDelayInSeconds": 90,
            "noTrafficTravelTimeInSeconds": 1650,
        },
        "legs": [],
    }
    result = _build_route_option(route)
    assert result["encoded_polyline"] == ""


def test_build_all_points_combines_routes():
    response = {
        "routes": [
            {
                "legs": [{"points": [{"latitude": 51.5, "longitude": -0.1}]}]
            },
            {
                "legs": [{"points": [{"latitude": 51.6, "longitude": -0.2}]}]
            },
        ]
    }
    pts = _build_all_points(response)
    assert len(pts) == 2


def test_build_all_points_missing_routes_returns_empty():
    assert _build_all_points({}) == []




# ---------------------------------------------------------------------------
# parse_incidents — edge cases for default values
# ---------------------------------------------------------------------------


def test_parse_incidents_incident_without_properties_key():
    # Verifies default {} is used when "properties" key is absent
    raw = [{}]
    # No properties → magnitude defaults to 0 → excluded
    assert parse_incidents(raw) == []


def test_parse_incidents_event_without_description_key():
    # Verifies description default "" is used when "description" key is absent in event
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 2,
                "iconCategory": "ACCIDENT",
                "events": [{}],  # event present but no "description" key
                "roadNumbers": ["M25"],
            }
        }
    ]
    result = parse_incidents(raw)
    assert result[0]["description"] == ""


# ---------------------------------------------------------------------------
# _parse_duration
# ---------------------------------------------------------------------------


def test_parse_duration_standard():
    assert _parse_duration("1800s") == 1800


def test_parse_duration_zero():
    assert _parse_duration("0s") == 0


def test_parse_duration_non_s_suffix_returns_zero():
    assert _parse_duration("1800") == 0


# ---------------------------------------------------------------------------
# _normalize_google_response
# ---------------------------------------------------------------------------

_GOOGLE_ROUTE = {
    "duration": "1800s",
    "staticDuration": "1650s",
    "distanceMeters": 25000,
    "legs": [
        {
            "startLocation": {"latLng": {"latitude": 51.5, "longitude": -0.1}},
            "endLocation": {"latLng": {"latitude": 51.55, "longitude": -0.15}},
            "steps": [
                {"navigationInstruction": {"instructions": "Head north on A3"}},
                {"navigationInstruction": {"instructions": "Join the M25"}},
                {"navigationInstruction": {"instructions": "Turn onto High Street"}},
            ],
        }
    ],
}

_GOOGLE_RESPONSE = {"routes": [_GOOGLE_ROUTE]}


def test_normalize_google_response_travel_time():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    assert result["routes"][0]["summary"]["travelTimeInSeconds"] == 1800


def test_normalize_google_response_no_traffic_time():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    assert result["routes"][0]["summary"]["noTrafficTravelTimeInSeconds"] == 1650


def test_normalize_google_response_delay():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    assert result["routes"][0]["summary"]["trafficDelayInSeconds"] == 150


def test_normalize_google_response_delay_never_negative():
    resp = {
        "routes": [
            {
                "duration": "1600s",
                "staticDuration": "1650s",
                "distanceMeters": 10000,
                "legs": [],
            }
        ]
    }
    result = _normalize_google_response(resp)
    assert result["routes"][0]["summary"]["trafficDelayInSeconds"] == 0


def test_normalize_google_response_distance():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    assert result["routes"][0]["summary"]["lengthInMeters"] == 25000


def test_normalize_google_response_traffic_model_id_empty():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    assert result["routes"][0]["summary"]["trafficModelId"] == ""


def test_normalize_google_response_extracts_motorway_and_a_road():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    road_names = [i["roadName"] for i in result["routes"][0]["legs"][0]["guidance"]["instructions"]]
    assert "A3" in road_names
    assert "M25" in road_names


def test_normalize_google_response_excludes_minor_roads():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    road_names = [i["roadName"] for i in result["routes"][0]["legs"][0]["guidance"]["instructions"]]
    # "High Street" should not appear — not an A or M road
    assert all(re.match(r"^[AM]\d", r) for r in road_names)


def test_normalize_google_response_points_from_start_end():
    result = _normalize_google_response(_GOOGLE_RESPONSE)
    points = result["routes"][0]["legs"][0]["points"]
    assert len(points) == 2
    assert points[0]["latitude"] == pytest.approx(51.5)
    assert points[1]["latitude"] == pytest.approx(51.55)


def test_normalize_google_response_empty_routes():
    result = _normalize_google_response({"routes": []})
    assert result["routes"] == []


def test_normalize_google_response_captures_encoded_polyline():
    resp = {
        "routes": [
            {
                "duration": "1800s",
                "staticDuration": "1650s",
                "distanceMeters": 25000,
                "polyline": {"encodedPolyline": "abc123"},
                "legs": [],
            }
        ]
    }
    result = _normalize_google_response(resp)
    assert result["routes"][0]["encoded_polyline"] == "abc123"


def test_normalize_google_response_missing_polyline_defaults_empty():
    resp = {
        "routes": [
            {
                "duration": "1800s",
                "staticDuration": "1650s",
                "distanceMeters": 25000,
                "legs": [],
            }
        ]
    }
    result = _normalize_google_response(resp)
    assert result["routes"][0]["encoded_polyline"] == ""


def test_normalize_google_response_multiple_routes():
    resp = {
        "routes": [
            {"duration": "1800s", "staticDuration": "1650s", "distanceMeters": 25000, "legs": []},
            {"duration": "1950s", "staticDuration": "1700s", "distanceMeters": 27000, "legs": []},
        ]
    }
    result = _normalize_google_response(resp)
    assert len(result["routes"]) == 2
    assert result["routes"][1]["summary"]["travelTimeInSeconds"] == 1950


def test_parse_incidents_incident_without_icon_category_key():
    # Verifies type defaults to "UNKNOWN" when "iconCategory" key is absent
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 2,
                "events": [],
                "roadNumbers": ["A3"],
            }
        }
    ]
    result = parse_incidents(raw)
    assert result[0]["type"] == "UNKNOWN"


def test_parse_incidents_road_empty_when_no_from_and_no_road_numbers():
    # Verifies road defaults to "" when "from" key absent and roadNumbers empty
    raw = [
        {
            "properties": {
                "magnitudeOfDelay": 2,
                "iconCategory": "CONGESTION",
                "events": [],
                "roadNumbers": [],
                # no "from" key
            }
        }
    ]
    result = parse_incidents(raw)
    assert result[0]["road"] == ""


# ---------------------------------------------------------------------------
# Helpers: shared mock data
# ---------------------------------------------------------------------------

_ROUTE_DATA = {
    "summary": {
        "lengthInMeters": 25000,
        "travelTimeInSeconds": 1800,
        "trafficDelayInSeconds": 90,
        "noTrafficTravelTimeInSeconds": 1650,
        "trafficModelId": "model-abc-123",
    },
    "legs": [
        {
            "points": [
                {"latitude": 51.5, "longitude": -0.1},
                {"latitude": 51.55, "longitude": -0.15},
            ],
            "guidance": {
                "instructions": [
                    {"roadName": "A3"},
                    {"roadName": "High Street"},
                    {"roadName": "M25"},
                ]
            },
        }
    ],
}

_ROUTE_DATA_ALT = {
    "summary": {
        "lengthInMeters": 27000,
        "travelTimeInSeconds": 1950,
        "trafficDelayInSeconds": 300,
        "noTrafficTravelTimeInSeconds": 1650,
        "trafficModelId": "model-abc-123",
    },
    "legs": [
        {
            "points": [
                {"latitude": 51.5, "longitude": -0.1},
                {"latitude": 51.6, "longitude": -0.2},
            ],
            "guidance": {
                "instructions": [
                    {"roadName": "A316"},
                ]
            },
        }
    ],
}

_ROUTES_RESPONSE = {"routes": [_ROUTE_DATA, _ROUTE_DATA_ALT]}

_INCIDENTS_RESPONSE = [
    {
        "properties": {
            "magnitudeOfDelay": 3,
            "iconCategory": "ACCIDENT",
            "events": [{"description": "Multi-vehicle accident"}],
            "roadNumbers": ["M25"],
        }
    }
]


# ---------------------------------------------------------------------------
# Endpoint integration tests
# ---------------------------------------------------------------------------


_CACHED_ROUTE_A = {
    "travel_time_seconds": 1800,
    "delay_seconds": 90,
    "distance_meters": 25000,
    "description": "via A3 and M25",
    "delay_colour": "green",
}

_CACHED_ROUTE_B = {
    "travel_time_seconds": 1950,
    "delay_seconds": 300,
    "distance_meters": 27000,
    "description": "via A316",
    "delay_colour": "amber",
}

_CACHED_INCIDENT = {
    "type": "ACCIDENT",
    "description": "Multi-vehicle accident",
    "road": "M25",
}

_CACHED_TRAVEL_DATA = {
    "home_to_work": [_CACHED_ROUTE_A, _CACHED_ROUTE_B],
    "home_to_nursery": [_CACHED_ROUTE_A, _CACHED_ROUTE_B],
    "incidents": [_CACHED_INCIDENT],
}


@patch("routers.travel._get_now")
def test_endpoint_returns_two_routes_for_each_commute(mock_now):
    import routers.travel as travel_module

    travel_module._cache = _CACHED_TRAVEL_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["home_to_work"]) == 2
    assert len(data["home_to_nursery"]) == 2
    travel_module._cache = None


@patch("routers.travel._get_now")
def test_endpoint_route_fields_present(mock_now):
    import routers.travel as travel_module

    travel_module._cache = _CACHED_TRAVEL_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    route = resp.json()["home_to_work"][0]
    assert "travel_time_seconds" in route
    assert "delay_seconds" in route
    assert "distance_meters" in route
    assert "description" in route
    assert "delay_colour" in route
    travel_module._cache = None


@patch("routers.travel._get_now")
def test_endpoint_route_description_extracted(mock_now):
    import routers.travel as travel_module

    travel_module._cache = _CACHED_TRAVEL_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.json()["home_to_work"][0]["description"] == "via A3 and M25"
    travel_module._cache = None


@patch("routers.travel._get_now")
def test_endpoint_incidents_returned(mock_now):
    import routers.travel as travel_module

    travel_module._cache = _CACHED_TRAVEL_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    data = resp.json()
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["type"] == "ACCIDENT"
    assert data["incidents"][0]["road"] == "M25"
    travel_module._cache = None


@patch("routers.travel._get_now")
def test_endpoint_no_incidents_when_empty(mock_now):
    import routers.travel as travel_module

    travel_module._cache = {**_CACHED_TRAVEL_DATA, "incidents": []}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.json()["incidents"] == []
    travel_module._cache = None


@patch("routers.travel._get_now")
def test_endpoint_not_stale_within_poll_window(mock_now):
    import routers.travel as travel_module

    travel_module._cache = _CACHED_TRAVEL_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.json()["is_stale"] is False
    travel_module._cache = None


@patch("scheduler.is_within_poll_window", return_value=False)
@patch("routers.travel._cache", new=None)
def test_endpoint_stale_outside_poll_window_no_cache(_mock_window):
    import routers.travel as travel_module

    travel_module._cache = None

    resp = client.get("/api/travel")
    assert resp.status_code == 200
    assert resp.json()["is_stale"] is True


@patch("scheduler.is_within_poll_window", return_value=False)
def test_endpoint_stale_outside_poll_window_with_cache(_mock_window):
    import routers.travel as travel_module

    travel_module._cache = {
        "home_to_work": [],
        "home_to_nursery": [],
        "incidents": [],
        "is_stale": False,
    }

    resp = client.get("/api/travel")
    assert resp.json()["is_stale"] is True

    # Cleanup
    travel_module._cache = None


@patch("routers.travel._get_now")
def test_endpoint_delay_colour_in_route(mock_now):
    import routers.travel as travel_module

    travel_module._cache = _CACHED_TRAVEL_DATA
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    # 90 delay / 1650 no-traffic = 5.5% → green (from cached data)
    assert resp.json()["home_to_work"][0]["delay_colour"] == "green"
    # 300 delay / 1650 no-traffic = 18.2% → amber
    assert resp.json()["home_to_work"][1]["delay_colour"] == "amber"
    travel_module._cache = None


# ---------------------------------------------------------------------------
# _normalize_here_response
# ---------------------------------------------------------------------------

_HERE_INCIDENT = {
    "type": "ACCIDENT",
    "criticality": 2,
    "description": {"value": "Multi-vehicle accident"},
    "location": {"description": {"value": "M25"}},
}


def test_normalize_here_response_basic():
    raw = {"results": [_HERE_INCIDENT]}
    result = _normalize_here_response(raw)
    assert len(result) == 1
    props = result[0]["properties"]
    assert props["magnitudeOfDelay"] == 2
    assert props["iconCategory"] == "ACCIDENT"
    assert props["events"][0]["description"] == "Multi-vehicle accident"
    assert props["from"] == "M25"
    assert props["roadNumbers"] == []


def test_normalize_here_response_empty_results():
    assert _normalize_here_response({"results": []}) == []


def test_normalize_here_response_missing_results_key():
    assert _normalize_here_response({}) == []


def test_normalize_here_response_major_criticality():
    raw = {"results": [{"type": "ROAD_CLOSED", "criticality": 3, "description": {"value": "Closure"}, "location": {"description": {"value": "A3"}}}]}
    result = _normalize_here_response(raw)
    assert result[0]["properties"]["magnitudeOfDelay"] == 3


def test_normalize_here_response_missing_criticality_defaults_zero():
    raw = {"results": [{"type": "UNKNOWN", "description": {"value": "Something"}, "location": {"description": {"value": "A3"}}}]}
    result = _normalize_here_response(raw)
    assert result[0]["properties"]["magnitudeOfDelay"] == 0


def test_normalize_here_response_missing_description():
    raw = {"results": [{"type": "CONGESTION", "criticality": 3, "location": {"description": {"value": "A3"}}}]}
    result = _normalize_here_response(raw)
    assert result[0]["properties"]["events"] == []


def test_normalize_here_response_missing_location():
    raw = {"results": [{"type": "ACCIDENT", "criticality": 2, "description": {"value": "Crash"}}]}
    result = _normalize_here_response(raw)
    assert result[0]["properties"]["from"] == ""


def test_normalize_here_response_missing_type_defaults_to_unknown():
    raw = {"results": [{"criticality": 2, "description": {"value": "Crash"}, "location": {"description": {"value": "M25"}}}]}
    result = _normalize_here_response(raw)
    assert result[0]["properties"]["iconCategory"] == "UNKNOWN"


def test_normalize_here_response_multiple_incidents():
    raw = {
        "results": [
            {"type": "ACCIDENT", "criticality": 3, "description": {"value": "Crash"}, "location": {"description": {"value": "M25"}}},
            {"type": "CONGESTION", "criticality": 2, "description": {"value": "Queue"}, "location": {"description": {"value": "A3"}}},
        ]
    }
    result = _normalize_here_response(raw)
    assert len(result) == 2
    assert result[0]["properties"]["from"] == "M25"
    assert result[1]["properties"]["from"] == "A3"


# ---------------------------------------------------------------------------
# fetch_incidents
# ---------------------------------------------------------------------------

_BBOX = {"min_lat": 51.4, "max_lat": 51.6, "min_lon": -0.3, "max_lon": 0.1}


def _make_here_client(resp_json: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.json.return_value = resp_json
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.mark.asyncio
async def test_fetch_incidents_returns_empty_when_no_api_key():
    mock_client = MagicMock()
    mock_client.get = AsyncMock()
    result = await fetch_incidents(mock_client, _BBOX, "")
    assert result == []
    mock_client.get.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_incidents_calls_here_api_url():
    mock_client = _make_here_client({"results": []})
    await fetch_incidents(mock_client, _BBOX, "test-key")
    url = mock_client.get.call_args[0][0]
    assert "data.traffic.hereapi.com" in url


@pytest.mark.asyncio
async def test_fetch_incidents_passes_bbox_as_query_param():
    mock_client = _make_here_client({"results": []})
    await fetch_incidents(mock_client, _BBOX, "test-key")
    params = mock_client.get.call_args[1]["params"]
    bbox_str = params["bbox"]
    assert "51.4" in bbox_str
    assert "-0.3" in bbox_str
    assert "51.6" in bbox_str
    assert "0.1" in bbox_str


@pytest.mark.asyncio
async def test_fetch_incidents_bbox_order_is_west_south_east_north():
    mock_client = _make_here_client({"results": []})
    await fetch_incidents(mock_client, _BBOX, "test-key")
    params = mock_client.get.call_args[1]["params"]
    parts = params["bbox"].split(",")
    # west=min_lon, south=min_lat, east=max_lon, north=max_lat
    assert float(parts[0]) == pytest.approx(-0.3)  # west (min_lon)
    assert float(parts[1]) == pytest.approx(51.4)  # south (min_lat)
    assert float(parts[2]) == pytest.approx(0.1)   # east (max_lon)
    assert float(parts[3]) == pytest.approx(51.6)  # north (max_lat)


@pytest.mark.asyncio
async def test_fetch_incidents_returns_normalized_incidents():
    here_resp = {
        "results": [
            {
                "type": "ACCIDENT",
                "criticality": 3,
                "description": {"value": "Crash on M25"},
                "location": {"description": {"value": "M25"}},
            }
        ]
    }
    mock_client = _make_here_client(here_resp)
    result = await fetch_incidents(mock_client, _BBOX, "test-key")
    assert len(result) == 1
    assert result[0]["properties"]["magnitudeOfDelay"] == 3
    assert result[0]["properties"]["iconCategory"] == "ACCIDENT"
    assert result[0]["properties"]["from"] == "M25"


@pytest.mark.asyncio
async def test_fetch_incidents_returns_empty_list_on_empty_results():
    mock_client = _make_here_client({"results": []})
    result = await fetch_incidents(mock_client, _BBOX, "test-key")
    assert result == []


@pytest.mark.asyncio
async def test_fetch_incidents_location_referencing_param_value():
    mock_client = _make_here_client({"results": []})
    await fetch_incidents(mock_client, _BBOX, "test-key")
    params = mock_client.get.call_args[1]["params"]
    assert params["locationReferencing"] == "shape"


@pytest.mark.asyncio
async def test_fetch_incidents_api_key_param_name_and_value():
    mock_client = _make_here_client({"results": []})
    await fetch_incidents(mock_client, _BBOX, "my-here-key")
    params = mock_client.get.call_args[1]["params"]
    assert params["apiKey"] == "my-here-key"
