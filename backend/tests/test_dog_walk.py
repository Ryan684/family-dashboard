"""Tests for dog walk route logic — feature: dog_walk.feature (pure logic)."""

import json
import os
import tempfile

from services.dog_walk import (
    is_dog_daycare_day,
    load_walk_routes,
    rank_routes,
    score_conditions,
)

SCHEDULE_WITH_WEDNESDAY_DAYCARE = {
    "dog_daycare": {"days": ["wednesday"], "weekly_dropper": "Commuter1"}
}

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


# ---------------------------------------------------------------------------
# is_dog_daycare_day
# ---------------------------------------------------------------------------


def test_is_dog_daycare_day_returns_true_on_daycare_day():
    assert is_dog_daycare_day("wednesday", SCHEDULE_WITH_WEDNESDAY_DAYCARE) is True


def test_is_dog_daycare_day_returns_false_on_non_daycare_day():
    assert is_dog_daycare_day("monday", SCHEDULE_WITH_WEDNESDAY_DAYCARE) is False


def test_is_dog_daycare_day_returns_false_on_tuesday():
    assert is_dog_daycare_day("tuesday", SCHEDULE_WITH_WEDNESDAY_DAYCARE) is False


def test_is_dog_daycare_day_returns_false_when_no_daycare_days():
    schedule = {"dog_daycare": {"days": [], "weekly_dropper": "Commuter1"}}
    assert is_dog_daycare_day("wednesday", schedule) is False


# ---------------------------------------------------------------------------
# score_conditions
# ---------------------------------------------------------------------------


def test_score_conditions_dry_when_both_below_threshold():
    label = score_conditions(
        precip_mm=5.0,
        soil_moisture=0.2,
        precip_threshold=10.0,
        soil_threshold=0.3,
    )
    assert label == "Dry"


def test_score_conditions_wet_when_precip_exceeds_threshold():
    label = score_conditions(
        precip_mm=15.0,
        soil_moisture=0.2,
        precip_threshold=10.0,
        soil_threshold=0.3,
    )
    assert label == "Wet"


def test_score_conditions_wet_when_soil_moisture_exceeds_threshold():
    label = score_conditions(
        precip_mm=5.0,
        soil_moisture=0.4,
        precip_threshold=10.0,
        soil_threshold=0.3,
    )
    assert label == "Wet"


def test_score_conditions_very_wet_when_both_exceed_threshold():
    label = score_conditions(
        precip_mm=15.0,
        soil_moisture=0.4,
        precip_threshold=10.0,
        soil_threshold=0.3,
    )
    assert label == "Very wet"


def test_score_conditions_dry_at_exact_threshold_boundary():
    label = score_conditions(
        precip_mm=10.0,
        soil_moisture=0.3,
        precip_threshold=10.0,
        soil_threshold=0.3,
    )
    assert label == "Dry"


def test_score_conditions_wet_just_above_precip_threshold():
    label = score_conditions(
        precip_mm=10.01,
        soil_moisture=0.1,
        precip_threshold=10.0,
        soil_threshold=0.3,
    )
    assert label == "Wet"


# ---------------------------------------------------------------------------
# rank_routes
# ---------------------------------------------------------------------------


def test_rank_routes_dry_all_routes_suitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Dry")
    assert all(r["suitable"] for r in ranked)


def test_rank_routes_wet_mud_sensitivity_3_unsuitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Wet")
    river = next(r for r in ranked if r["id"] == "river-trail")
    assert river["suitable"] is False


def test_rank_routes_wet_mud_sensitivity_1_still_suitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Wet")
    park = next(r for r in ranked if r["id"] == "park-loop")
    assert park["suitable"] is True


def test_rank_routes_wet_mud_sensitivity_2_still_suitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Wet")
    mixed = next(r for r in ranked if r["id"] == "mixed-loop")
    assert mixed["suitable"] is True


def test_rank_routes_very_wet_mud_sensitivity_2_unsuitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Very wet")
    mixed = next(r for r in ranked if r["id"] == "mixed-loop")
    assert mixed["suitable"] is False


def test_rank_routes_very_wet_mud_sensitivity_3_unsuitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Very wet")
    river = next(r for r in ranked if r["id"] == "river-trail")
    assert river["suitable"] is False


def test_rank_routes_very_wet_mud_sensitivity_1_suitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Very wet")
    park = next(r for r in ranked if r["id"] == "park-loop")
    assert park["suitable"] is True


def test_rank_routes_suitable_routes_before_unsuitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Wet")
    suitable_indices = [i for i, r in enumerate(ranked) if r["suitable"]]
    unsuitable_indices = [i for i, r in enumerate(ranked) if not r["suitable"]]
    if suitable_indices and unsuitable_indices:
        assert max(suitable_indices) < min(unsuitable_indices)


def test_rank_routes_unknown_conditions_all_suitable():
    ranked = rank_routes(SAMPLE_ROUTES, "Unknown")
    assert all(r["suitable"] for r in ranked)


def test_rank_routes_empty_routes_returns_empty():
    assert rank_routes([], "Dry") == []


def test_rank_routes_very_wet_route_missing_mud_sensitivity_defaults_to_suitable():
    # mud_sensitivity absent → defaults to 1, so suitable under "Very wet" (threshold 2)
    route = {"id": "no-sens", "name": "No Sensitivity Route", "duration_minutes": 30, "distance_km": 2.5}
    ranked = rank_routes([route], "Very wet")
    assert ranked[0]["suitable"] is True


# ---------------------------------------------------------------------------
# load_walk_routes
# ---------------------------------------------------------------------------


def test_load_walk_routes_returns_list_from_file():
    data = {"routes": SAMPLE_ROUTES}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(data, f)
        path = f.name
    try:
        routes = load_walk_routes(path)
        assert len(routes) == 3
        assert routes[0]["id"] == "park-loop"
    finally:
        os.unlink(path)


def test_load_walk_routes_returns_empty_list_for_empty_config():
    data = {"routes": []}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(data, f)
        path = f.name
    try:
        routes = load_walk_routes(path)
        assert routes == []
    finally:
        os.unlink(path)
