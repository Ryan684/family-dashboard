"""Tests for the dynamic per-commuter travel endpoint and fetch_travel_data."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

_ROUTE_DATA = {
    "summary": {
        "lengthInMeters": 25000,
        "travelTimeInSeconds": 1800,
        "trafficDelayInSeconds": 90,
        "noTrafficTravelTimeInSeconds": 1650,
        "trafficModelId": "model-abc",
    },
    "legs": [
        {
            "points": [
                {"latitude": 51.5, "longitude": -0.1},
                {"latitude": 51.55, "longitude": -0.15},
            ],
            "guidance": {"instructions": [{"roadName": "A3"}, {"roadName": "M25"}]},
        }
    ],
}

_ROUTE_DATA_ALT = {
    "summary": {
        "lengthInMeters": 27000,
        "travelTimeInSeconds": 1950,
        "trafficDelayInSeconds": 300,
        "noTrafficTravelTimeInSeconds": 1650,
        "trafficModelId": "model-abc",
    },
    "legs": [
        {
            "points": [
                {"latitude": 51.5, "longitude": -0.1},
                {"latitude": 51.6, "longitude": -0.2},
            ],
            "guidance": {"instructions": [{"roadName": "A316"}]},
        }
    ],
}

_ROUTES_RESPONSE = {"routes": [_ROUTE_DATA, _ROUTE_DATA_ALT]}

_INCIDENT_RAW = [
    {
        "properties": {
            "magnitudeOfDelay": 3,
            "iconCategory": "ACCIDENT",
            "events": [{"description": "Multi-vehicle accident"}],
            "roadNumbers": ["M25"],
        }
    }
]

_CACHED_COMMUTER = {
    "name": "Ryan",
    "mode": "office",
    "drops": [],
    "routes": [
        {
            "travel_time_seconds": 1800,
            "delay_seconds": 90,
            "distance_meters": 25000,
            "description": "via A3 and M25",
            "delay_colour": "green",
        }
    ],
    "incidents": [],
}

# ---------------------------------------------------------------------------
# Endpoint — GET /api/travel
# ---------------------------------------------------------------------------


@patch("routers.travel._get_now")
def test_endpoint_returns_commuters_array(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = {"commuters": [_CACHED_COMMUTER]}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.status_code == 200
    data = resp.json()
    assert "commuters" in data
    assert len(data["commuters"]) == 1
    travel_mod._cache = None


@patch("routers.travel._get_now")
def test_endpoint_commuter_has_required_fields(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = {"commuters": [_CACHED_COMMUTER]}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    commuter = resp.json()["commuters"][0]
    assert "name" in commuter
    assert "mode" in commuter
    assert "drops" in commuter
    assert "routes" in commuter
    assert "incidents" in commuter
    travel_mod._cache = None


@patch("routers.travel._get_now")
def test_endpoint_empty_commuters_when_no_cache(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = None
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["commuters"] == []
    travel_mod._cache = None


@patch("routers.travel._get_now")
def test_endpoint_is_stale_false_within_window(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = {"commuters": [_CACHED_COMMUTER]}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.json()["is_stale"] is False
    travel_mod._cache = None


@patch("routers.travel._get_now")
def test_endpoint_is_stale_true_outside_window(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = {"commuters": [_CACHED_COMMUTER]}
    mock_now.return_value = datetime(2025, 1, 1, 12, 0, 0)

    resp = client.get("/api/travel")
    assert resp.json()["is_stale"] is True
    travel_mod._cache = None


@patch("routers.travel._get_now")
def test_endpoint_two_commuters_in_response(mock_now):
    import routers.travel as travel_mod

    commuter2 = {**_CACHED_COMMUTER, "name": "Emily"}
    travel_mod._cache = {"commuters": [_CACHED_COMMUTER, commuter2]}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    names = [c["name"] for c in resp.json()["commuters"]]
    assert "Ryan" in names
    assert "Emily" in names
    travel_mod._cache = None


@patch("routers.travel._get_now")
def test_endpoint_empty_commuters_array_when_all_wfh(mock_now):
    import routers.travel as travel_mod

    travel_mod._cache = {"commuters": []}
    mock_now.return_value = datetime(2025, 1, 1, 7, 30, 0)

    resp = client.get("/api/travel")
    assert resp.json()["commuters"] == []
    travel_mod._cache = None


# ---------------------------------------------------------------------------
# fetch_travel_data integration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_travel_data_office_no_drops():
    """Office commuter with no drops → home → work route, included in response."""
    schedule = {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {"monday": {"mode": "office", "nursery_drop": False}},
            }
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": [], "weekly_dropper": ""},
    }
    coords = {
        "home": (51.5, -0.1),
        "work": {"Ryan": (51.52, -0.08)},
        "nursery": (51.51, -0.09),
        "dog_daycare": (51.53, -0.07),
    }

    with (
        patch("routers.travel.load_schedule", return_value=schedule),
        patch("routers.travel.get_coords", return_value=coords),
        patch("routers.travel._get_weekday", return_value="monday"),
        patch("routers.travel.fetch_routes", new_callable=AsyncMock, return_value=_ROUTES_RESPONSE),
        patch("routers.travel.fetch_incidents", new_callable=AsyncMock, return_value=_INCIDENT_RAW),
    ):
        from routers.travel import fetch_travel_data
        result = await fetch_travel_data()

    assert len(result["commuters"]) == 1
    commuter = result["commuters"][0]
    assert commuter["name"] == "Ryan"
    assert commuter["mode"] == "office"
    assert commuter["drops"] == []
    assert len(commuter["routes"]) == 2


@pytest.mark.asyncio
async def test_fetch_travel_data_wfh_no_drops_excluded():
    """WFH commuter with no drops is excluded from commuters array."""
    schedule = {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {"monday": {"mode": "wfh", "nursery_drop": False}},
            }
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": [], "weekly_dropper": ""},
    }
    coords = {
        "home": (51.5, -0.1),
        "work": {"Ryan": (51.52, -0.08)},
        "nursery": (51.51, -0.09),
        "dog_daycare": (51.53, -0.07),
    }

    with (
        patch("routers.travel.load_schedule", return_value=schedule),
        patch("routers.travel.get_coords", return_value=coords),
        patch("routers.travel._get_weekday", return_value="monday"),
    ):
        from routers.travel import fetch_travel_data
        result = await fetch_travel_data()

    assert result["commuters"] == []


@pytest.mark.asyncio
async def test_fetch_travel_data_office_with_nursery_drop():
    """Office commuter with nursery drop → waypoints include nursery."""
    schedule = {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": ["nursery"],
                "schedule": {"monday": {"mode": "office", "nursery_drop": True}},
            }
        ],
        "nursery": {"days": ["monday"]},
        "dog_daycare": {"days": [], "weekly_dropper": ""},
    }
    coords = {
        "home": (51.5, -0.1),
        "work": {"Ryan": (51.52, -0.08)},
        "nursery": (51.51, -0.09),
        "dog_daycare": (51.53, -0.07),
    }

    captured_waypoints = []

    async def mock_fetch_routes(client, waypoints, api_key):
        captured_waypoints.extend(waypoints)
        return _ROUTES_RESPONSE

    with (
        patch("routers.travel.load_schedule", return_value=schedule),
        patch("routers.travel.get_coords", return_value=coords),
        patch("routers.travel._get_weekday", return_value="monday"),
        patch("routers.travel.fetch_routes", side_effect=mock_fetch_routes),
        patch("routers.travel.fetch_incidents", new_callable=AsyncMock, return_value=[]),
    ):
        from routers.travel import fetch_travel_data
        result = await fetch_travel_data()

    assert result["commuters"][0]["drops"] == ["nursery"]
    # waypoints: home, nursery, work
    assert coords["nursery"] in captured_waypoints


@pytest.mark.asyncio
async def test_fetch_travel_data_off_no_drops_excluded():
    """Day-off commuter with no drops is excluded from commuters array."""
    schedule = {
        "commuters": [
            {
                "name": "Emily",
                "drop_order": [],
                "schedule": {"monday": {"mode": "off", "nursery_drop": False}},
            }
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": [], "weekly_dropper": ""},
    }
    coords = {
        "home": (51.5, -0.1),
        "work": {"Emily": (51.48, -0.12)},
        "nursery": (51.51, -0.09),
        "dog_daycare": (51.53, -0.07),
    }

    with (
        patch("routers.travel.load_schedule", return_value=schedule),
        patch("routers.travel.get_coords", return_value=coords),
        patch("routers.travel._get_weekday", return_value="monday"),
    ):
        from routers.travel import fetch_travel_data
        result = await fetch_travel_data()

    assert result["commuters"] == []


@pytest.mark.asyncio
async def test_fetch_travel_data_first_wfh_second_active():
    """First commuter WFH (empty waypoints) must not stop processing of second commuter."""
    schedule = {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {"monday": {"mode": "wfh", "nursery_drop": False}},
            },
            {
                "name": "Emily",
                "drop_order": [],
                "schedule": {"monday": {"mode": "office", "nursery_drop": False}},
            },
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": [], "weekly_dropper": ""},
    }
    coords = {
        "home": (51.5, -0.1),
        "work": {"Ryan": (51.52, -0.08), "Emily": (51.48, -0.12)},
        "nursery": (51.51, -0.09),
        "dog_daycare": (51.53, -0.07),
    }

    with (
        patch("routers.travel.load_schedule", return_value=schedule),
        patch("routers.travel.get_coords", return_value=coords),
        patch("routers.travel._get_weekday", return_value="monday"),
        patch("routers.travel.fetch_routes", new_callable=AsyncMock, return_value=_ROUTES_RESPONSE),
        patch("routers.travel.fetch_incidents", new_callable=AsyncMock, return_value=[]),
    ):
        from routers.travel import fetch_travel_data
        result = await fetch_travel_data()

    assert len(result["commuters"]) == 1
    assert result["commuters"][0]["name"] == "Emily"


@pytest.mark.asyncio
async def test_fetch_travel_data_both_commuters_active():
    """Two active office commuters both appear in the response."""
    schedule = {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {"monday": {"mode": "office", "nursery_drop": False}},
            },
            {
                "name": "Emily",
                "drop_order": [],
                "schedule": {"monday": {"mode": "office", "nursery_drop": False}},
            },
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": [], "weekly_dropper": ""},
    }
    coords = {
        "home": (51.5, -0.1),
        "work": {"Ryan": (51.52, -0.08), "Emily": (51.48, -0.12)},
        "nursery": (51.51, -0.09),
        "dog_daycare": (51.53, -0.07),
    }

    with (
        patch("routers.travel.load_schedule", return_value=schedule),
        patch("routers.travel.get_coords", return_value=coords),
        patch("routers.travel._get_weekday", return_value="monday"),
        patch("routers.travel.fetch_routes", new_callable=AsyncMock, return_value=_ROUTES_RESPONSE),
        patch("routers.travel.fetch_incidents", new_callable=AsyncMock, return_value=[]),
    ):
        from routers.travel import fetch_travel_data
        result = await fetch_travel_data()

    assert len(result["commuters"]) == 2
    names = [c["name"] for c in result["commuters"]]
    assert "Ryan" in names
    assert "Emily" in names
