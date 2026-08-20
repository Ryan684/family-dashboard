"""Tests for the Met Office NSWWS severe weather warnings integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.nswws import (
    filter_warnings_for_points,
    fetch_warnings,
    parse_warnings,
    sort_warnings,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Squares in GeoJSON [lon, lat] order. Home sits at (-0.1, 51.5).
_COVERS_HOME = [[[-1.0, 51.0], [-1.0, 52.0], [1.0, 52.0], [1.0, 51.0], [-1.0, 51.0]]]
# Ryan's office at (-0.2, 51.6) — this one covers both.
_COVERS_ELSEWHERE = [
    [[10.0, 10.0], [10.0, 11.0], [11.0, 11.0], [11.0, 10.0], [10.0, 10.0]]
]

_HOME = {"name": "Home", "lat": 51.5, "lon": -0.1}
_OFFICE = {"name": "Guildford", "lat": 51.6, "lon": -0.2}


def _feature(
    warning_id="w1",
    level="AMBER",
    weather_type="rain",
    headline="Heavy rain may cause flooding",
    status=None,
    coordinates=None,
):
    properties = {
        "warningId": warning_id,
        "warningLevel": level,
        "weatherType": weather_type,
        "warningHeadline": headline,
        "issuedDate": "2026-08-20T09:00:00Z",
        "validFromDate": "2026-08-21T06:00:00Z",
        "validToDate": "2026-08-21T18:00:00Z",
    }
    if status is not None:
        properties["warningStatus"] = status
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": coordinates or [_COVERS_HOME],
        },
    }


def _collection(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def _make_client(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status = MagicMock()
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    return client


def _warning(level="AMBER", warning_id="w1", coordinates=None, headline="Heavy rain"):
    return {
        "id": warning_id,
        "level": level,
        "weather_type": "rain",
        "headline": headline,
        "issued": "2026-08-20T09:00:00Z",
        "valid_from": "2026-08-21T06:00:00Z",
        "valid_to": "2026-08-21T18:00:00Z",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": coordinates or [_COVERS_HOME],
        },
    }


# ---------------------------------------------------------------------------
# fetch_warnings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_warnings_without_a_key_returns_empty():
    client = _make_client(_collection(_feature()))
    assert await fetch_warnings(client, "") == []


@pytest.mark.asyncio
async def test_fetch_warnings_without_a_key_makes_no_request():
    client = _make_client(_collection(_feature()))
    await fetch_warnings(client, "")
    client.get.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_warnings_with_a_key_makes_a_request():
    client = _make_client(_collection(_feature()))
    await fetch_warnings(client, "secret-key")
    client.get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_warnings_sends_the_key_as_a_header():
    client = _make_client(_collection(_feature()))
    await fetch_warnings(client, "secret-key")
    assert client.get.call_args[1]["headers"]["x-api-key"] == "secret-key"


@pytest.mark.asyncio
async def test_fetch_warnings_returns_parsed_warnings():
    client = _make_client(_collection(_feature(headline="Heavy rain")))
    result = await fetch_warnings(client, "secret-key")
    assert result[0]["headline"] == "Heavy rain"


@pytest.mark.asyncio
async def test_fetch_warnings_raises_for_status():
    client = _make_client(_collection())
    await fetch_warnings(client, "secret-key")
    client.get.return_value.raise_for_status.assert_called_once()


# ---------------------------------------------------------------------------
# parse_warnings
# ---------------------------------------------------------------------------


def test_parse_warnings_extracts_the_id():
    assert parse_warnings(_collection(_feature(warning_id="abc")))[0]["id"] == "abc"


def test_parse_warnings_extracts_the_level():
    assert parse_warnings(_collection(_feature(level="RED")))[0]["level"] == "RED"


def test_parse_warnings_extracts_the_weather_type():
    result = parse_warnings(_collection(_feature(weather_type="wind")))
    assert result[0]["weather_type"] == "wind"


def test_parse_warnings_extracts_the_headline():
    result = parse_warnings(_collection(_feature(headline="Strong winds")))
    assert result[0]["headline"] == "Strong winds"


def test_parse_warnings_extracts_the_geometry():
    result = parse_warnings(_collection(_feature()))
    assert result[0]["geometry"]["type"] == "MultiPolygon"


def test_parse_warnings_extracts_the_validity_period():
    result = parse_warnings(_collection(_feature()))
    assert result[0]["valid_from"] == "2026-08-21T06:00:00Z"
    assert result[0]["valid_to"] == "2026-08-21T18:00:00Z"


def test_parse_warnings_upper_cases_the_level():
    assert parse_warnings(_collection(_feature(level="amber")))[0]["level"] == "AMBER"


def test_parse_warnings_empty_collection_returns_empty():
    assert parse_warnings(_collection()) == []


def test_parse_warnings_missing_features_key_returns_empty():
    assert parse_warnings({}) == []


def test_parse_warnings_feature_without_properties_is_skipped():
    assert parse_warnings(_collection({"type": "Feature"})) == []


def test_parse_warnings_discards_a_cancelled_warning():
    assert parse_warnings(_collection(_feature(status="Cancelled"))) == []


def test_parse_warnings_discards_an_expired_warning():
    assert parse_warnings(_collection(_feature(status="Expired"))) == []


def test_parse_warnings_status_check_is_case_insensitive():
    assert parse_warnings(_collection(_feature(status="cancelled"))) == []


def test_parse_warnings_keeps_a_warning_with_no_status():
    assert len(parse_warnings(_collection(_feature()))) == 1


def test_parse_warnings_keeps_an_issued_warning():
    assert len(parse_warnings(_collection(_feature(status="Issued")))) == 1


def test_parse_warnings_falls_back_to_a_composite_id():
    feature = _feature()
    del feature["properties"]["warningId"]
    result = parse_warnings(_collection(feature))
    assert result[0]["id"] == "AMBER|rain|2026-08-20T09:00:00Z|Heavy rain may cause flooding"


def test_parse_warnings_returns_multiple_warnings_in_feed_order():
    result = parse_warnings(
        _collection(_feature(warning_id="a"), _feature(warning_id="b"))
    )
    assert [w["id"] for w in result] == ["a", "b"]


# ---------------------------------------------------------------------------
# filter_warnings_for_points
# ---------------------------------------------------------------------------


def test_filter_keeps_a_warning_covering_home():
    result = filter_warnings_for_points([_warning()], [_HOME])
    assert len(result) == 1


def test_filter_names_the_matched_location():
    result = filter_warnings_for_points([_warning()], [_HOME])
    assert result[0]["locations"] == ["Home"]


def test_filter_discards_a_warning_covering_nothing_of_ours():
    warning = _warning(coordinates=[_COVERS_ELSEWHERE])
    assert filter_warnings_for_points([warning], [_HOME, _OFFICE]) == []


def test_filter_returns_one_entry_for_several_matched_locations():
    result = filter_warnings_for_points([_warning()], [_HOME, _OFFICE])
    assert len(result) == 1


def test_filter_lists_every_matched_location():
    result = filter_warnings_for_points([_warning()], [_HOME, _OFFICE])
    assert result[0]["locations"] == ["Home", "Guildford"]


def test_filter_deduplicates_a_repeated_location_name():
    # The same coordinate appears in both today's and tomorrow's lists.
    result = filter_warnings_for_points([_warning()], [_HOME, _HOME])
    assert result[0]["locations"] == ["Home"]


def test_filter_preserves_feed_order():
    warnings = [_warning(warning_id="a"), _warning(warning_id="b")]
    result = filter_warnings_for_points(warnings, [_HOME])
    assert [w["id"] for w in result] == ["a", "b"]


def test_filter_with_no_points_returns_empty():
    assert filter_warnings_for_points([_warning()], []) == []


def test_filter_with_no_warnings_returns_empty():
    assert filter_warnings_for_points([], [_HOME]) == []


def test_filter_drops_the_geometry_from_the_payload():
    # The frontend has no use for a MultiPolygon; sending it would bloat every poll.
    result = filter_warnings_for_points([_warning()], [_HOME])
    assert "geometry" not in result[0]


# ---------------------------------------------------------------------------
# sort_warnings
# ---------------------------------------------------------------------------


def test_sort_warnings_puts_red_before_amber():
    result = sort_warnings([_warning(level="AMBER"), _warning(level="RED")])
    assert [w["level"] for w in result] == ["RED", "AMBER"]


def test_sort_warnings_puts_amber_before_yellow():
    result = sort_warnings([_warning(level="YELLOW"), _warning(level="AMBER")])
    assert [w["level"] for w in result] == ["AMBER", "YELLOW"]


def test_sort_warnings_preserves_feed_order_within_a_level():
    result = sort_warnings(
        [_warning(level="AMBER", warning_id="a"), _warning(level="AMBER", warning_id="b")]
    )
    assert [w["id"] for w in result] == ["a", "b"]


def test_sort_warnings_puts_an_unknown_level_last():
    result = sort_warnings([_warning(level="MYSTERY"), _warning(level="YELLOW")])
    assert [w["level"] for w in result] == ["YELLOW", "MYSTERY"]


def test_sort_warnings_empty_list():
    assert sort_warnings([]) == []
