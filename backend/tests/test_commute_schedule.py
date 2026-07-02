"""Tests for commute schedule resolver — schedule loading, gate rules, waypoint building."""

import json
import pytest
from unittest.mock import patch, mock_open

from services.commute_schedule import (
    load_schedule,
    resolve_commuter_day,
    build_waypoints,
)

# ---------------------------------------------------------------------------
# Fixtures — minimal schedule config
# ---------------------------------------------------------------------------

SCHEDULE = {
    "commuters": [
        {
            "name": "Ryan",
            "drop_order": ["dog", "nursery"],
            "schedule": {
                "monday":    {"mode": "office", "nursery_drop": True,  "dog_drop": False},
                "tuesday":   {"mode": "office", "nursery_drop": False, "dog_drop": False},
                "wednesday": {"mode": "off",    "nursery_drop": False, "dog_drop": True},
                "thursday":  {"mode": "office", "nursery_drop": True,  "dog_drop": False},
                "friday":    {"mode": "wfh",    "nursery_drop": False, "dog_drop": False},
            },
        },
        {
            "name": "Emily",
            "drop_order": ["nursery", "dog"],
            "schedule": {
                "monday":    {"mode": "office", "nursery_drop": False, "dog_drop": False},
                "tuesday":   {"mode": "office", "nursery_drop": True,  "dog_drop": False},
                "wednesday": {"mode": "office", "nursery_drop": False, "dog_drop": False},
                "thursday":  {"mode": "wfh",    "nursery_drop": False, "dog_drop": False},
                "friday":    {"mode": "off",    "nursery_drop": False, "dog_drop": False},
            },
        },
    ],
    "nursery": {"days": ["monday", "tuesday", "thursday"]},
    "dog_daycare": {"days": ["wednesday"]},
}

COORDS = {
    "home": (51.5, -0.1),
    "work": {"Ryan": (51.52, -0.08), "Emily": (51.48, -0.12)},
    "nursery": (51.51, -0.09),
    "dog_daycare": (51.53, -0.07),
}

# ---------------------------------------------------------------------------
# load_schedule
# ---------------------------------------------------------------------------


def test_load_schedule_returns_parsed_json(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(SCHEDULE))
    result = load_schedule(str(config_file))
    assert result["commuters"][0]["name"] == "Ryan"
    assert result["nursery"]["days"] == ["monday", "tuesday", "thursday"]


# ---------------------------------------------------------------------------
# resolve_commuter_day — mode
# ---------------------------------------------------------------------------


def test_resolve_office_day_no_drops():
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "tuesday", SCHEDULE)
    assert result["mode"] == "office"
    assert result["drops"] == []


def test_resolve_office_monday_only_nursery_drop():
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "monday", SCHEDULE)
    assert result["mode"] == "office"
    assert result["drops"] == ["nursery"]


def test_resolve_wfh_day_no_drops():
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "friday", SCHEDULE)
    assert result["mode"] == "wfh"
    assert result["drops"] == []


def test_resolve_off_day_no_drops():
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "wednesday", SCHEDULE)
    assert result["mode"] == "off"
    # wednesday is dog daycare day and Ryan is weekly_dropper
    assert result["drops"] == ["dog"]


def test_resolve_office_with_dog_drop_false():
    # Emily is office on wednesday, but dog_drop is False — no dog drop
    result = resolve_commuter_day(SCHEDULE["commuters"][1], "wednesday", SCHEDULE)
    assert result["mode"] == "office"
    assert "dog" not in result["drops"]


# ---------------------------------------------------------------------------
# Nursery gate
# ---------------------------------------------------------------------------


def test_nursery_gate_blocks_drop_when_not_nursery_day():
    # Tuesday is a nursery day for Emily, but let's test a non-nursery day
    # Ryan has nursery_drop=True on monday which IS a nursery day → included
    # Ryan on tuesday: nursery_drop=False → excluded regardless
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "tuesday", SCHEDULE)
    assert "nursery" not in result["drops"]


def test_nursery_gate_blocks_when_today_not_in_nursery_days():
    # Use a schedule where nursery_drop=True but today not in nursery.days
    schedule = {**SCHEDULE, "nursery": {"days": ["tuesday"]}}  # monday NOT a nursery day
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "monday", schedule)
    assert "nursery" not in result["drops"]


def test_nursery_gate_allows_when_today_in_nursery_days_and_flag_true():
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "monday", SCHEDULE)
    assert "nursery" in result["drops"]


# ---------------------------------------------------------------------------
# Dog gate
# ---------------------------------------------------------------------------


def test_dog_gate_blocks_when_not_dog_day():
    # Ryan on monday: monday not in dog_daycare.days → no dog
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "monday", SCHEDULE)
    assert "dog" not in result["drops"]


def test_dog_gate_blocks_when_dog_drop_false():
    # Emily on wednesday: dog day but dog_drop is False
    result = resolve_commuter_day(SCHEDULE["commuters"][1], "wednesday", SCHEDULE)
    assert "dog" not in result["drops"]


def test_dog_gate_allows_when_dog_day_and_dog_drop_true():
    # Ryan on wednesday: dog day and dog_drop is True
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "wednesday", SCHEDULE)
    assert "dog" in result["drops"]


# ---------------------------------------------------------------------------
# Drop ordering
# ---------------------------------------------------------------------------


def test_drop_order_dog_first_for_ryan():
    # Thursday: nursery_drop=True AND dog_drop=True → dog comes first per drop_order
    ryan = {
        **SCHEDULE["commuters"][0],
        "schedule": {
            **SCHEDULE["commuters"][0]["schedule"],
            "thursday": {"mode": "office", "nursery_drop": True, "dog_drop": True},
        },
    }
    schedule = {**SCHEDULE, "dog_daycare": {"days": ["thursday"]}}
    result = resolve_commuter_day(ryan, "thursday", schedule)
    assert result["drops"] == ["dog", "nursery"]


def test_drop_order_nursery_first_for_emily():
    # Emily with nursery and dog on same day — nursery first per her drop_order
    emily = {
        **SCHEDULE["commuters"][1],
        "schedule": {
            **SCHEDULE["commuters"][1]["schedule"],
            "tuesday": {"mode": "office", "nursery_drop": True, "dog_drop": True},
        },
    }
    schedule = {**SCHEDULE, "dog_daycare": {"days": ["tuesday"]}}
    result = resolve_commuter_day(emily, "tuesday", schedule)
    assert result["drops"] == ["nursery", "dog"]


# ---------------------------------------------------------------------------
# Default fallback coverage (kills mutmut survivors on .get() defaults)
# ---------------------------------------------------------------------------


def test_resolve_unknown_weekday_defaults_to_off():
    """Missing weekday key in schedule → default mode is 'off', not something else."""
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "sunday", SCHEDULE)
    assert result["mode"] == "off"


def test_resolve_unknown_weekday_default_nursery_drop_is_false():
    """Missing weekday → nursery_drop defaults to False, so even if today is nursery day, no drop."""
    schedule = {**SCHEDULE, "nursery": {"days": ["sunday"]}}
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "sunday", schedule)
    assert "nursery" not in result["drops"]


def test_resolve_unknown_weekday_default_dog_drop_is_false():
    """Missing weekday → dog_drop defaults to False, so even if today is dog daycare day, no drop."""
    schedule = {**SCHEDULE, "dog_daycare": {"days": ["sunday"]}}
    result = resolve_commuter_day(SCHEDULE["commuters"][0], "sunday", schedule)
    assert "dog" not in result["drops"]


def test_resolve_commuter_without_drop_order_key():
    """Commuter missing drop_order key → defaults to empty list, no drops ordered."""
    commuter = {
        "name": "Ryan",
        # no drop_order key
        "schedule": {"monday": {"mode": "office", "nursery_drop": True}},
    }
    result = resolve_commuter_day(commuter, "monday", SCHEDULE)
    assert result["drops"] == []


# ---------------------------------------------------------------------------
# build_waypoints
# ---------------------------------------------------------------------------


def test_build_waypoints_office_no_drops():
    waypoints = build_waypoints(
        mode="office",
        drops=[],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [COORDS["home"], COORDS["work"]["Ryan"]]


def test_build_waypoints_office_nursery_only():
    waypoints = build_waypoints(
        mode="office",
        drops=["nursery"],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [COORDS["home"], COORDS["nursery"], COORDS["work"]["Ryan"]]


def test_build_waypoints_office_dog_only():
    waypoints = build_waypoints(
        mode="office",
        drops=["dog"],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [COORDS["home"], COORDS["dog_daycare"], COORDS["work"]["Ryan"]]


def test_build_waypoints_office_dog_then_nursery():
    waypoints = build_waypoints(
        mode="office",
        drops=["dog", "nursery"],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [
        COORDS["home"],
        COORDS["dog_daycare"],
        COORDS["nursery"],
        COORDS["work"]["Ryan"],
    ]


def test_build_waypoints_office_nursery_then_dog():
    waypoints = build_waypoints(
        mode="office",
        drops=["nursery", "dog"],
        home=COORDS["home"],
        work=COORDS["work"]["Emily"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [
        COORDS["home"],
        COORDS["nursery"],
        COORDS["dog_daycare"],
        COORDS["work"]["Emily"],
    ]


def test_build_waypoints_wfh_no_drops_returns_empty():
    waypoints = build_waypoints(
        mode="wfh",
        drops=[],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == []


def test_build_waypoints_off_no_drops_returns_empty():
    waypoints = build_waypoints(
        mode="off",
        drops=[],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == []


def test_build_waypoints_wfh_dog_out_and_back():
    waypoints = build_waypoints(
        mode="wfh",
        drops=["dog"],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [COORDS["home"], COORDS["dog_daycare"], COORDS["home"]]


def test_build_waypoints_wfh_nursery_out_and_back():
    waypoints = build_waypoints(
        mode="wfh",
        drops=["nursery"],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [COORDS["home"], COORDS["nursery"], COORDS["home"]]


def test_build_waypoints_off_both_drops_out_and_back():
    waypoints = build_waypoints(
        mode="off",
        drops=["dog", "nursery"],
        home=COORDS["home"],
        work=COORDS["work"]["Ryan"],
        nursery=COORDS["nursery"],
        dog_daycare=COORDS["dog_daycare"],
    )
    assert waypoints == [
        COORDS["home"],
        COORDS["dog_daycare"],
        COORDS["nursery"],
        COORDS["home"],
    ]


# ---------------------------------------------------------------------------
# departure_time in resolve_commuter_day
# ---------------------------------------------------------------------------

_SCHEDULE_WITH_DEPARTURE = {
    "commuters": [
        {
            "name": "Ryan",
            "drop_order": [],
            "schedule": {
                "monday": {"mode": "office", "nursery_drop": False, "departure_time": "07:30"},
                "tuesday": {"mode": "office", "nursery_drop": False},
            },
        }
    ],
    "nursery": {"days": []},
    "dog_daycare": {"days": []},
}


def test_resolve_commuter_day_returns_departure_time_when_set():
    result = resolve_commuter_day(
        _SCHEDULE_WITH_DEPARTURE["commuters"][0], "monday", _SCHEDULE_WITH_DEPARTURE
    )
    assert result["departure_time"] == "07:30"


def test_resolve_commuter_day_returns_none_departure_time_when_not_set():
    result = resolve_commuter_day(
        _SCHEDULE_WITH_DEPARTURE["commuters"][0], "tuesday", _SCHEDULE_WITH_DEPARTURE
    )
    assert result["departure_time"] is None


def test_resolve_commuter_day_returns_none_departure_time_for_unknown_day():
    result = resolve_commuter_day(
        _SCHEDULE_WITH_DEPARTURE["commuters"][0], "sunday", _SCHEDULE_WITH_DEPARTURE
    )
    assert result["departure_time"] is None


# ---------------------------------------------------------------------------
# load_schedule — departure_time validation
# ---------------------------------------------------------------------------

def _schedule_with_departure_time(value):
    return {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {
                    "friday": {"mode": "office", "nursery_drop": False, "departure_time": value},
                },
            }
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": []},
    }


def _schedule_without_departure_time():
    return {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {
                    "friday": {"mode": "office", "nursery_drop": False},
                },
            }
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": []},
    }


def test_load_schedule_accepts_valid_hhmm_departure_time(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_with_departure_time("07:25")))
    result = load_schedule(str(config_file))
    assert result["commuters"][0]["schedule"]["friday"]["departure_time"] == "07:25"


def test_load_schedule_rejects_single_digit_hour(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_with_departure_time("7:25")))
    with pytest.raises(ValueError):
        load_schedule(str(config_file))


def test_load_schedule_accepts_absent_departure_time(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_without_departure_time()))
    result = load_schedule(str(config_file))
    assert "departure_time" not in result["commuters"][0]["schedule"]["friday"]


def test_load_schedule_error_message_contains_context(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_with_departure_time("7:25")))
    with pytest.raises(ValueError, match="Ryan") as exc_info:
        load_schedule(str(config_file))
    message = str(exc_info.value)
    assert "friday" in message
    assert "7:25" in message


# ---------------------------------------------------------------------------
# arrive_by in resolve_commuter_day
# ---------------------------------------------------------------------------

_SCHEDULE_WITH_ARRIVE_BY = {
    "commuters": [
        {
            "name": "Ryan",
            "drop_order": [],
            "schedule": {
                "monday": {"mode": "office", "nursery_drop": False, "arrive_by": "09:00"},
                "tuesday": {"mode": "office", "nursery_drop": False},
            },
        }
    ],
    "nursery": {"days": []},
    "dog_daycare": {"days": []},
}


def test_resolve_commuter_day_returns_arrive_by_when_set():
    result = resolve_commuter_day(
        _SCHEDULE_WITH_ARRIVE_BY["commuters"][0], "monday", _SCHEDULE_WITH_ARRIVE_BY
    )
    assert result["arrive_by"] == "09:00"


def test_resolve_commuter_day_returns_none_arrive_by_when_not_set():
    result = resolve_commuter_day(
        _SCHEDULE_WITH_ARRIVE_BY["commuters"][0], "tuesday", _SCHEDULE_WITH_ARRIVE_BY
    )
    assert result["arrive_by"] is None


def test_resolve_commuter_day_returns_none_arrive_by_for_unknown_day():
    result = resolve_commuter_day(
        _SCHEDULE_WITH_ARRIVE_BY["commuters"][0], "sunday", _SCHEDULE_WITH_ARRIVE_BY
    )
    assert result["arrive_by"] is None


# ---------------------------------------------------------------------------
# load_schedule — arrive_by validation
# ---------------------------------------------------------------------------

def _schedule_with_arrive_by(value):
    return {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {
                    "friday": {"mode": "office", "nursery_drop": False, "arrive_by": value},
                },
            }
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": []},
    }


def _schedule_without_arrive_by():
    return {
        "commuters": [
            {
                "name": "Ryan",
                "drop_order": [],
                "schedule": {
                    "friday": {"mode": "office", "nursery_drop": False},
                },
            }
        ],
        "nursery": {"days": []},
        "dog_daycare": {"days": []},
    }


def test_load_schedule_accepts_valid_hhmm_arrive_by(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_with_arrive_by("09:00")))
    result = load_schedule(str(config_file))
    assert result["commuters"][0]["schedule"]["friday"]["arrive_by"] == "09:00"


def test_load_schedule_rejects_single_digit_hour_arrive_by(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_with_arrive_by("9:00")))
    with pytest.raises(ValueError):
        load_schedule(str(config_file))


def test_load_schedule_accepts_absent_arrive_by(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_without_arrive_by()))
    result = load_schedule(str(config_file))
    assert "arrive_by" not in result["commuters"][0]["schedule"]["friday"]


def test_load_schedule_arrive_by_error_message_contains_context(tmp_path):
    config_file = tmp_path / "commute-schedule.json"
    config_file.write_text(json.dumps(_schedule_with_arrive_by("9:00")))
    with pytest.raises(ValueError, match="Ryan") as exc_info:
        load_schedule(str(config_file))
    message = str(exc_info.value)
    assert "friday" in message
    assert "9:00" in message
