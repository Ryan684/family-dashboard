"""Tests for dog walk API endpoint — feature: dog_walk.feature (endpoint)."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _mock_conditions(precip_mm=5.0, soil_moisture=0.2, available=True):
    return {"precip_mm": precip_mm, "soil_moisture": soil_moisture, "available": available}


SAMPLE_ROUTES = [
    {
        "id": "park-loop",
        "name": "Park Loop",
        "description": "Flat pavement path",
        "duration_minutes": 25,
        "distance_km": 2.1,
        "surface": "pavement",
        "mud_sensitivity": 1,
    },
    {
        "id": "river-trail",
        "name": "River Trail",
        "description": "Muddy riverside path",
        "duration_minutes": 45,
        "distance_km": 3.8,
        "surface": "trail",
        "mud_sensitivity": 3,
    },
    {
        "id": "mixed-loop",
        "name": "Mixed Loop",
        "description": "Half pavement, half trail",
        "duration_minutes": 35,
        "distance_km": 3.0,
        "surface": "mixed",
        "mud_sensitivity": 2,
    },
]


@pytest.fixture()
def routes_file(tmp_path):
    data = {"routes": SAMPLE_ROUTES}
    path = tmp_path / "walk-routes.json"
    path.write_text(json.dumps(data))
    return str(path)


@pytest.fixture()
def empty_routes_file(tmp_path):
    data = {"routes": []}
    path = tmp_path / "walk-routes.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_endpoint_not_eligible_on_daycare_day(routes_file):
    with (
        patch("routers.dog_walk.get_today_weekday", return_value="wednesday"),
        patch("routers.dog_walk.WALK_ROUTES_PATH", routes_file),
        patch(
            "routers.dog_walk.fetch_conditions",
            new=AsyncMock(return_value=_mock_conditions()),
        ),
    ):
        resp = client.get("/api/dog-walk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["eligible"] is False
    assert data["routes"] == []


def test_endpoint_eligible_on_non_daycare_day(routes_file):
    with (
        patch("routers.dog_walk.get_today_weekday", return_value="monday"),
        patch("routers.dog_walk.WALK_ROUTES_PATH", routes_file),
        patch(
            "routers.dog_walk.fetch_conditions",
            new=AsyncMock(return_value=_mock_conditions()),
        ),
    ):
        resp = client.get("/api/dog-walk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["eligible"] is True
    assert len(data["routes"]) == 3


def test_endpoint_dry_conditions_all_routes_suitable(routes_file):
    with (
        patch("routers.dog_walk.get_today_weekday", return_value="monday"),
        patch("routers.dog_walk.WALK_ROUTES_PATH", routes_file),
        patch(
            "routers.dog_walk.fetch_conditions",
            new=AsyncMock(return_value=_mock_conditions(precip_mm=5.0, soil_moisture=0.2)),
        ),
    ):
        resp = client.get("/api/dog-walk")
    data = resp.json()
    assert data["conditions"] == "Dry"
    assert all(r["suitable"] for r in data["routes"])


def test_endpoint_wet_conditions_marks_high_sensitivity_unsuitable(routes_file):
    with (
        patch("routers.dog_walk.get_today_weekday", return_value="monday"),
        patch("routers.dog_walk.WALK_ROUTES_PATH", routes_file),
        patch(
            "routers.dog_walk.fetch_conditions",
            new=AsyncMock(return_value=_mock_conditions(precip_mm=15.0, soil_moisture=0.2)),
        ),
    ):
        resp = client.get("/api/dog-walk")
    data = resp.json()
    assert data["conditions"] == "Wet"
    river = next(r for r in data["routes"] if r["id"] == "river-trail")
    assert river["suitable"] is False
    park = next(r for r in data["routes"] if r["id"] == "park-loop")
    assert park["suitable"] is True


def test_endpoint_conditions_unavailable_defaults_to_unknown(routes_file):
    with (
        patch("routers.dog_walk.get_today_weekday", return_value="monday"),
        patch("routers.dog_walk.WALK_ROUTES_PATH", routes_file),
        patch(
            "routers.dog_walk.fetch_conditions",
            new=AsyncMock(return_value=_mock_conditions(available=False)),
        ),
    ):
        resp = client.get("/api/dog-walk")
    data = resp.json()
    assert data["conditions"] == "Unknown"
    assert all(r["suitable"] for r in data["routes"])


def test_endpoint_empty_routes_config_returns_empty_list(empty_routes_file):
    with (
        patch("routers.dog_walk.get_today_weekday", return_value="monday"),
        patch("routers.dog_walk.WALK_ROUTES_PATH", empty_routes_file),
        patch(
            "routers.dog_walk.fetch_conditions",
            new=AsyncMock(return_value=_mock_conditions()),
        ),
    ):
        resp = client.get("/api/dog-walk")
    data = resp.json()
    assert data["eligible"] is True
    assert data["routes"] == []
