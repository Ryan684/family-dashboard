"""Tests for the Met Office NSWWS severe weather warnings integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.nswws import (
    filter_warnings_for_points,
    fetch_warnings,
    parse_feed_related_url,
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
    headline="Heavy rain may cause flooding",
    status=None,
    coordinates=None,
    impact=2,
    likelihood=2,
    weather_type=("RAIN",),
):
    properties = {
        "warningId": warning_id,
        "warningLevel": level,
        "warningHeadline": headline,
        "issuedDate": "2026-08-20T09:00:00Z",
        "validFromDate": "2026-08-21T06:00:00Z",
        "validToDate": "2026-08-21T18:00:00Z",
        "warningImpact": impact,
        "warningLikelihood": likelihood,
        "weatherType": list(weather_type),
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


_WARNINGS_URL = "https://api.example/v1.0/objects/issued/3f4ca4cf/"


def _feed_xml(related_url=_WARNINGS_URL, include_related=True):
    """A minimal Atom feed matching the real docs' shape, feed-level links only."""
    related = (
        f'<link rel="related" type="application/vnd.geo+json" '
        f'href="{related_url}" title="Latest version of all issued warnings" />'
        if include_related
        else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Met Office Warnings Feed</title>
    <link rel="self" type="application/atom+xml" href="https://api.example/v1.0/objects/feed/" />
    {related}
    <id>urn:uuid:f6b54389-c75c-4f23-aa21-88ef3481761a</id>
    <updated>2022-06-16T13:39:02Z</updated>
</feed>"""


def _feed_xml_with_entry():
    """A feed carrying one <entry>, whose own rel="alternate" link must never
    be mistaken for the feed-level rel="related" link."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Met Office Warnings Feed</title>
    <link rel="self" type="application/atom+xml" href="https://api.example/v1.0/objects/feed/" />
    <link rel="related" type="application/vnd.geo+json" href="{_WARNINGS_URL}" title="Latest version of all issued warnings" />
    <id>urn:uuid:f6b54389-c75c-4f23-aa21-88ef3481761a</id>
    <updated>2022-06-16T13:39:02Z</updated>
    <entry>
        <title>Update</title>
        <link rel="alternate" type="application/vnd.geo+json" href="https://api.example/v1.0/objects/updated/entry-only/" title="Warnings Updated" />
        <id>urn:uuid:c9ce3dca-13e0-4eaf-8f74-cf44ec04279c</id>
        <updated>2022-06-15T23:00:10Z</updated>
        <summary>Warnings update.</summary>
    </entry>
</feed>"""


def _make_feed_client(feed_xml=None, geojson_payload=None):
    """A client whose first client.get() returns the Atom feed, second the
    GeoJSON it points to — matching fetch_warnings's real two-step fetch.

    Returns (client, feed_response, geojson_response) so callers that need to
    assert against the individual mock responses (e.g. raise_for_status) can,
    without indexing into the AsyncMock's already-consumed side_effect list."""
    feed_response = MagicMock()
    feed_response.text = _feed_xml() if feed_xml is None else feed_xml
    feed_response.raise_for_status = MagicMock()

    geojson_response = MagicMock()
    geojson_response.json.return_value = (
        _collection(_feature()) if geojson_payload is None else geojson_payload
    )
    geojson_response.raise_for_status = MagicMock()

    client = MagicMock()
    client.get = AsyncMock(side_effect=[feed_response, geojson_response])
    return client, feed_response, geojson_response


def _warning(
    level="AMBER",
    warning_id="w1",
    coordinates=None,
    headline="Heavy rain",
    impact=2,
    likelihood=2,
    weather_types=("rain",),
):
    return {
        "id": warning_id,
        "level": level,
        "headline": headline,
        "issued": "2026-08-20T09:00:00Z",
        "valid_from": "2026-08-21T06:00:00Z",
        "valid_to": "2026-08-21T18:00:00Z",
        "impact": impact,
        "likelihood": likelihood,
        "weather_types": list(weather_types),
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
    client, _, _ = _make_feed_client()
    assert await fetch_warnings(client, "", "https://api.example") == []


@pytest.mark.asyncio
async def test_fetch_warnings_without_a_key_makes_no_request():
    client, _, _ = _make_feed_client()
    await fetch_warnings(client, "", "https://api.example")
    client.get.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_warnings_without_a_base_url_returns_empty():
    client, _, _ = _make_feed_client()
    assert await fetch_warnings(client, "secret-key", "") == []


@pytest.mark.asyncio
async def test_fetch_warnings_without_a_base_url_makes_no_request():
    client, _, _ = _make_feed_client()
    await fetch_warnings(client, "secret-key", "")
    client.get.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_warnings_makes_exactly_two_requests():
    # One for the Atom feed, one for the GeoJSON URL it points to.
    client, _, _ = _make_feed_client()
    await fetch_warnings(client, "secret-key", "https://api.example")
    assert client.get.call_count == 2


@pytest.mark.asyncio
async def test_fetch_warnings_first_request_is_the_feed_endpoint():
    client, _, _ = _make_feed_client()
    await fetch_warnings(client, "secret-key", "https://api.example")
    assert client.get.call_args_list[0][0][0] == "https://api.example/v1.0/objects/feed"


@pytest.mark.asyncio
async def test_fetch_warnings_second_request_is_the_feeds_related_url():
    # Not a composed URL — the exact href the feed supplied, since it rotates.
    client, _, _ = _make_feed_client(feed_xml=_feed_xml(related_url="https://api.example/v1.0/objects/issued/some-uuid/"))
    await fetch_warnings(client, "secret-key", "https://api.example")
    assert client.get.call_args_list[1][0][0] == "https://api.example/v1.0/objects/issued/some-uuid/"


@pytest.mark.asyncio
async def test_fetch_warnings_sends_the_key_as_a_header_on_both_requests():
    client, _, _ = _make_feed_client()
    await fetch_warnings(client, "secret-key", "https://api.example")
    for call in client.get.call_args_list:
        assert call[1]["headers"]["x-api-key"] == "secret-key"


@pytest.mark.asyncio
async def test_fetch_warnings_returns_parsed_warnings():
    client, _, _ = _make_feed_client(
        geojson_payload=_collection(_feature(headline="Heavy rain"))
    )
    result = await fetch_warnings(client, "secret-key", "https://api.example")
    assert result[0]["headline"] == "Heavy rain"


@pytest.mark.asyncio
async def test_fetch_warnings_raises_for_status_on_the_feed_request():
    client, feed_response, _ = _make_feed_client()
    await fetch_warnings(client, "secret-key", "https://api.example")
    feed_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_warnings_raises_for_status_on_the_geojson_request():
    client, _, geojson_response = _make_feed_client()
    await fetch_warnings(client, "secret-key", "https://api.example")
    geojson_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_warnings_missing_related_link_returns_empty():
    client, _, _ = _make_feed_client(feed_xml=_feed_xml(include_related=False))
    assert await fetch_warnings(client, "secret-key", "https://api.example") == []


@pytest.mark.asyncio
async def test_fetch_warnings_missing_related_link_makes_no_second_request():
    client, _, _ = _make_feed_client(feed_xml=_feed_xml(include_related=False))
    await fetch_warnings(client, "secret-key", "https://api.example")
    assert client.get.call_count == 1


@pytest.mark.asyncio
async def test_fetch_warnings_malformed_feed_returns_empty():
    client, _, _ = _make_feed_client(feed_xml="not xml at all")
    assert await fetch_warnings(client, "secret-key", "https://api.example") == []


@pytest.mark.asyncio
async def test_fetch_warnings_ignores_an_entrys_own_alternate_link():
    # The entry's rel="alternate" link must never be followed instead of the
    # feed-level rel="related" one.
    client, _, _ = _make_feed_client(feed_xml=_feed_xml_with_entry())
    await fetch_warnings(client, "secret-key", "https://api.example")
    assert client.get.call_args_list[1][0][0] == _WARNINGS_URL


# ---------------------------------------------------------------------------
# parse_feed_related_url
# ---------------------------------------------------------------------------


def test_parse_feed_related_url_returns_the_related_href():
    assert parse_feed_related_url(_feed_xml()) == _WARNINGS_URL


def test_parse_feed_related_url_ignores_an_entrys_alternate_link():
    # Only the feed-level rel="related" link counts, never an <entry>'s own
    # rel="alternate" — that describes one past change, not the current set.
    assert parse_feed_related_url(_feed_xml_with_entry()) == _WARNINGS_URL


def test_parse_feed_related_url_returns_none_for_malformed_xml():
    assert parse_feed_related_url("not xml at all") is None


def test_parse_feed_related_url_returns_none_when_missing():
    assert parse_feed_related_url(_feed_xml(include_related=False)) is None


def test_parse_feed_related_url_present_even_with_no_entries():
    # The docs' own "no events" example feed has zero <entry> elements but
    # still carries the feed-level related link — entries and the related
    # link are independent, so an empty feed must not be treated as absent.
    feed_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>Met Office Warnings Feed</title>
    <link rel="self" type="application/atom+xml" href="https://api.example/v1.0/objects/feed/" />
    <link rel="related" type="application/vnd.geo+json" href="{url}" title="Latest version of all issued warnings" />
    <id>urn:uuid:f6b54389-c75c-4f23-aa21-88ef3481761a</id>
    <updated>2022-06-16T13:39:02Z</updated>
</feed>""".format(url=_WARNINGS_URL)
    assert parse_feed_related_url(feed_xml) == _WARNINGS_URL


# ---------------------------------------------------------------------------
# parse_warnings
# ---------------------------------------------------------------------------


def test_parse_warnings_extracts_the_id():
    assert parse_warnings(_collection(_feature(warning_id="abc")))[0]["id"] == "abc"


def test_parse_warnings_extracts_the_level():
    assert parse_warnings(_collection(_feature(level="RED")))[0]["level"] == "RED"


def test_parse_warnings_extracts_the_impact():
    result = parse_warnings(_collection(_feature(impact=3)))
    assert result[0]["impact"] == 3


def test_parse_warnings_extracts_the_likelihood():
    result = parse_warnings(_collection(_feature(likelihood=1)))
    assert result[0]["likelihood"] == 1


def test_parse_warnings_extracts_the_weather_types():
    result = parse_warnings(_collection(_feature(weather_type=("THUNDERSTORM",))))
    assert result[0]["weather_types"] == ["THUNDERSTORM"]


def test_parse_warnings_extracts_multiple_weather_types():
    result = parse_warnings(_collection(_feature(weather_type=("WIND", "RAIN"))))
    assert result[0]["weather_types"] == ["WIND", "RAIN"]


def test_parse_warnings_missing_weather_type_becomes_empty_list():
    assert parse_warnings(_collection(_bare_feature()))[0]["weather_types"] == []


def test_parse_warnings_non_list_weather_type_becomes_empty_list():
    # Defends against the classic string/list mixup: iterating a bare string
    # would silently produce one bogus single-character "type" per character.
    feature = _feature()
    feature["properties"]["weatherType"] = "RAIN"
    assert parse_warnings(_collection(feature))[0]["weather_types"] == []


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
    assert result[0]["id"] == "AMBER|2026-08-20T09:00:00Z|Heavy rain may cause flooding"


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


def test_sort_warnings_breaks_a_level_tie_by_higher_impact():
    result = sort_warnings(
        [_warning(level="AMBER", warning_id="low", impact=1),
         _warning(level="AMBER", warning_id="high", impact=3)]
    )
    assert [w["id"] for w in result] == ["high", "low"]


def test_sort_warnings_breaks_an_impact_tie_by_higher_likelihood():
    result = sort_warnings(
        [_warning(level="AMBER", warning_id="low", impact=2, likelihood=1),
         _warning(level="AMBER", warning_id="high", impact=2, likelihood=3)]
    )
    assert [w["id"] for w in result] == ["high", "low"]


def test_sort_warnings_level_always_outranks_impact():
    # A lower-impact RED still beats a higher-impact AMBER.
    result = sort_warnings(
        [_warning(level="AMBER", warning_id="amber", impact=3),
         _warning(level="RED", warning_id="red", impact=1)]
    )
    assert [w["id"] for w in result] == ["red", "amber"]


def test_sort_warnings_missing_impact_sorts_as_least_severe():
    result = sort_warnings(
        [_warning(level="AMBER", warning_id="unknown", impact=None),
         _warning(level="AMBER", warning_id="known", impact=1)]
    )
    assert [w["id"] for w in result] == ["known", "unknown"]


def test_sort_warnings_missing_impact_sorts_after_the_lowest_real_value():
    # A missing rating must lose even to the lowest real rating NSWWS uses (1),
    # not just to higher ones — feeding "unknown" first pins the direction
    # regardless of input order, which a merely lower sentinel could still get
    # backwards if the sentinel sits too close to a real minimum value.
    result = sort_warnings(
        [_warning(level="AMBER", warning_id="unknown", impact=None, likelihood=2),
         _warning(level="AMBER", warning_id="known", impact=1, likelihood=2)]
    )
    assert [w["id"] for w in result] == ["known", "unknown"]


def test_sort_warnings_missing_likelihood_sorts_after_the_lowest_real_value():
    result = sort_warnings(
        [_warning(level="AMBER", warning_id="unknown", impact=2, likelihood=None),
         _warning(level="AMBER", warning_id="known", impact=2, likelihood=1)]
    )
    assert [w["id"] for w in result] == ["known", "unknown"]


# ---------------------------------------------------------------------------
# Defensive parsing — field names are confirmed against a real captured
# response (see module docstring), but a captured sample is not a schema
# guarantee, so a feature missing any field must still degrade cleanly rather
# than raise.
# ---------------------------------------------------------------------------


def _bare_feature():
    """A feature with a properties block but nothing useful in it."""
    return {"type": "Feature", "properties": {"warningId": "bare"}}


def test_parse_warnings_missing_level_becomes_empty_string():
    assert parse_warnings(_collection(_bare_feature()))[0]["level"] == ""


def test_parse_warnings_missing_impact_becomes_none():
    assert parse_warnings(_collection(_bare_feature()))[0]["impact"] is None


def test_parse_warnings_missing_likelihood_becomes_none():
    assert parse_warnings(_collection(_bare_feature()))[0]["likelihood"] is None


def test_parse_warnings_non_numeric_impact_becomes_none():
    feature = _bare_feature()
    feature["properties"]["warningImpact"] = "moderate"
    assert parse_warnings(_collection(feature))[0]["impact"] is None


def test_parse_warnings_missing_headline_becomes_empty_string():
    assert parse_warnings(_collection(_bare_feature()))[0]["headline"] == ""


def test_parse_warnings_missing_issued_becomes_empty_string():
    assert parse_warnings(_collection(_bare_feature()))[0]["issued"] == ""


def test_parse_warnings_missing_valid_from_becomes_empty_string():
    assert parse_warnings(_collection(_bare_feature()))[0]["valid_from"] == ""


def test_parse_warnings_missing_valid_to_becomes_empty_string():
    assert parse_warnings(_collection(_bare_feature()))[0]["valid_to"] == ""


def test_parse_warnings_missing_geometry_becomes_empty_dict():
    assert parse_warnings(_collection(_bare_feature()))[0]["geometry"] == {}


def test_parse_warnings_extracts_the_issued_date():
    result = parse_warnings(_collection(_feature()))
    assert result[0]["issued"] == "2026-08-20T09:00:00Z"


def test_parse_warnings_skips_a_bad_feature_and_keeps_later_ones():
    # A malformed feature must not abandon the rest of the feed.
    result = parse_warnings(
        _collection({"type": "Feature"}, _feature(warning_id="good"))
    )
    assert [w["id"] for w in result] == ["good"]


def test_parse_warnings_keeps_features_after_a_cancelled_one():
    result = parse_warnings(
        _collection(_feature(warning_id="dead", status="Cancelled"),
                    _feature(warning_id="live"))
    )
    assert [w["id"] for w in result] == ["live"]


# ---------------------------------------------------------------------------
# Defensive matching and fetching
# ---------------------------------------------------------------------------


def test_filter_warning_without_a_geometry_is_excluded():
    warning = {key: value for key, value in _warning().items() if key != "geometry"}
    assert filter_warnings_for_points([warning], [_HOME]) == []
