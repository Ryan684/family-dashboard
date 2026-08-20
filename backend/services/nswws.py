"""Met Office NSWWS (National Severe Weather Warning Service) integration.

Open-Meteo has no alerts endpoint, so severe weather warnings come from here.

NSWWS is a NATIONAL feed — every live UK warning, with a GeoJSON MultiPolygon
per warning and no way to query by coordinate. Narrowing it to the places this
household actually goes is done locally, in `filter_warnings_for_points`.

The API key is obtained by application rather than self-serve, so everything
here degrades to an empty list when no key is configured. That keeps the feature
mergeable and testable before the key exists, and means adding the key to .env
is the only step needed to switch it on.
"""

import httpx

from services.geo import point_in_geometry

NSWWS_BASE = "https://api.metoffice.gov.uk/nswws"

# Statuses that mean the warning is no longer in force.
_DEAD_STATUSES = frozenset({"cancelled", "expired"})

# Most severe first. Anything unrecognised sorts last rather than being guessed at.
_LEVEL_ORDER = {"RED": 0, "AMBER": 1, "YELLOW": 2}


def parse_warnings(feed: dict) -> list[dict]:
    """Flatten an NSWWS GeoJSON FeatureCollection into warning dicts.

    Warnings that are no longer in force are dropped here rather than by the
    caller, so nothing downstream has to know about NSWWS status vocabulary.

    Every field is read defensively: this parses a feed shape that has not been
    observed against the live API yet, and a missing key must not take down the
    poll loop.
    """
    warnings = []

    for feature in feed.get("features", []):
        properties = feature.get("properties")
        if not properties:
            continue

        status = str(properties.get("warningStatus", "")).lower()
        if status in _DEAD_STATUSES:
            continue

        level = str(properties.get("warningLevel", "")).upper()
        weather_type = properties.get("weatherType", "")
        headline = properties.get("warningHeadline", "")
        issued = properties.get("issuedDate", "")

        warnings.append(
            {
                # The feed's own id where it has one. The composite fallback can
                # collide if a warning is reissued unchanged, which is harmless:
                # the two would be identical anyway.
                "id": properties.get("warningId")
                or f"{level}|{weather_type}|{issued}|{headline}",
                "level": level,
                "weather_type": weather_type,
                "headline": headline,
                "issued": issued,
                "valid_from": properties.get("validFromDate", ""),
                "valid_to": properties.get("validToDate", ""),
                "geometry": feature.get("geometry", {}),
            }
        )

    return warnings


def filter_warnings_for_points(warnings: list[dict], points: list[dict]) -> list[dict]:
    """Keep warnings whose area covers at least one of our locations.

    `points` are {"name", "lat", "lon"} — today's and tomorrow's weather
    locations combined, so an amber wind warning over an office 40 miles away
    still surfaces on a commute dashboard.

    Each warning appears at most once however many of our locations it covers,
    tagged with their names so the banner can say where. Names are deduplicated
    because the same place usually appears in both days' lists.

    The geometry is dropped from the result: the frontend has no use for a
    MultiPolygon and shipping one would bloat every poll.
    """
    matched = []

    for warning in warnings:
        geometry = warning.get("geometry", {})
        names: list[str] = []
        for point in points:
            # geo takes longitude first, matching GeoJSON's [lon, lat] order.
            if point_in_geometry(point["lon"], point["lat"], geometry):
                if point["name"] not in names:
                    names.append(point["name"])

        if names:
            matched.append(
                {key: value for key, value in warning.items() if key != "geometry"}
                | {"locations": names}
            )

    return matched


def sort_warnings(warnings: list[dict]) -> list[dict]:
    """Most severe first, preserving feed order within a level."""
    return sorted(
        warnings, key=lambda w: _LEVEL_ORDER.get(w.get("level", ""), len(_LEVEL_ORDER))
    )


async def fetch_warnings(client: httpx.AsyncClient, api_key: str) -> list[dict]:
    """Fetch live UK severe weather warnings from NSWWS.

    Returns an empty list if no API key is configured.
    """
    if not api_key:
        return []

    resp = await client.get(
        f"{NSWWS_BASE}/warnings",
        headers={"x-api-key": api_key},
    )
    resp.raise_for_status()
    return parse_warnings(resp.json())
