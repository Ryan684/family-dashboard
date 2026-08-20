"""Met Office NSWWS (National Severe Weather Warning Service) integration.

Open-Meteo has no alerts endpoint, so severe weather warnings come from here.

NSWWS is a NATIONAL feed — every live UK warning, with a GeoJSON MultiPolygon
per warning and no way to query by coordinate. Narrowing it to the places this
household actually goes is done locally, in `filter_warnings_for_points`.

The API key is obtained by application rather than self-serve, so everything
here degrades to an empty list when no key is configured. That keeps the feature
mergeable and testable before the key exists, and means adding the key to .env
is the only step needed to switch it on.

Field names are confirmed against a real captured NSWWS response (found via
GitHub code search — repatterning/warning's checked-in data/latest.geojson and
its System NamedTuple, both dated November 2025 — since the API's own docs site
is unreachable from this development environment's network policy). Confirmed:
warningId, warningLevel, warningStatus, warningHeadline, issuedDate,
validFromDate, validToDate, warningImpact, warningLikelihood, geometry as
MultiPolygon with [lon, lat] coordinate order. There is no "weatherType" or
similar hazard-category field — the hazard only appears as free text inside the
headline.

warningImpact/warningLikelihood direction: an official metoffice.gov.uk page
(also found via search, describing impact as very low/low/medium/high)
corroborates higher = more severe, independently of the field names above —
sort_warnings assumes that direction.

Still open, and now the bigger unknown of the two: the exact request shape.
This module calls a single GET returning one GeoJSON FeatureCollection of every
live warning, filtering out dead ones by warningStatus. But repatterning/warning
— the same real client the field names above came from — never reads
warningStatus at all: it parses NSWWS's Atom feed, and only follows the <link>
entries whose href contains "issued", to discover per-warning GeoJSON URLs one
at a time. That implies live/cancelled/expired may be encoded by which Atom
link exists, not by inspecting a status property on a combined endpoint — which
would mean fetch_warnings's shape needs rework once this is confirmed, not just
its field parsing. Kept as the simpler single-endpoint design for now (matching
the "GeoJSON ... properties" description search also surfaced, which may
describe a genuinely different, simpler endpoint this client just doesn't use)
rather than rewritten speculatively on one third-party client's implementation
choice. The exact warningStatus literal values (cancelled/expired) are
consequently still unconfirmed by any source found so far — the parser's
comparison is case-insensitive but still exact-match, so casing alone ("CANCELLED"
vs "cancelled") doesn't matter, but a different word entirely would.
"""

import httpx

from services.geo import point_in_geometry

NSWWS_BASE = "https://api.metoffice.gov.uk/nswws"

# Statuses that mean the warning is no longer in force. The exact literal
# values NSWWS uses here are unconfirmed — see module docstring.
_DEAD_STATUSES = frozenset({"cancelled", "expired"})

# Most severe first. Anything unrecognised sorts last rather than being guessed at.
_LEVEL_ORDER = {"RED": 0, "AMBER": 1, "YELLOW": 2}


def _as_int(value) -> int | None:
    """Best-effort int conversion for the impact/likelihood ratings.

    None rather than a crash or a silently-wrong 0 when the value is absent or
    not actually numeric — a bad tie-breaker should never take down parsing.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_warnings(feed: dict) -> list[dict]:
    """Flatten an NSWWS GeoJSON FeatureCollection into warning dicts.

    Warnings that are no longer in force are dropped here rather than by the
    caller, so nothing downstream has to know about NSWWS status vocabulary.

    Every field is still read defensively despite the confirmed shape (see
    module docstring): a captured sample is not a schema guarantee, and a
    missing key must not take down the poll loop.
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
        headline = properties.get("warningHeadline", "")
        issued = properties.get("issuedDate", "")

        warnings.append(
            {
                # The feed's own id where it has one. The composite fallback can
                # collide if a warning is reissued unchanged, which is harmless:
                # the two would be identical anyway.
                "id": properties.get("warningId") or f"{level}|{issued}|{headline}",
                "level": level,
                "headline": headline,
                "issued": issued,
                "valid_from": properties.get("validFromDate", ""),
                "valid_to": properties.get("validToDate", ""),
                "impact": _as_int(properties.get("warningImpact")),
                "likelihood": _as_int(properties.get("warningLikelihood")),
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


def _sort_key(indexed_warning: tuple[int, dict]) -> tuple:
    index, warning = indexed_warning
    return (
        _LEVEL_ORDER.get(warning.get("level", ""), len(_LEVEL_ORDER)),
        -(warning.get("impact") or -1),
        -(warning.get("likelihood") or -1),
        index,
    )


def sort_warnings(warnings: list[dict]) -> list[dict]:
    """Most severe first: level, then impact, then likelihood, matching the
    priority Met Office's own docs describe for ranking warnings. Missing
    impact/likelihood sort as least severe among ties rather than raising.
    Feed order is preserved for anything left tied after all three.
    """
    return [w for _, w in sorted(enumerate(warnings), key=_sort_key)]


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
