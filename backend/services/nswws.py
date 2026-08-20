"""Met Office NSWWS (National Severe Weather Warning Service) integration.

Open-Meteo has no alerts endpoint, so severe weather warnings come from here.

NSWWS is a NATIONAL feed — every live UK warning, with a GeoJSON MultiPolygon
per warning and no way to query by coordinate. Narrowing it to the places this
household actually goes is done locally, in `filter_warnings_for_points`.

The API key is obtained by application rather than self-serve, so everything
here degrades to an empty list when no key is configured. That keeps the feature
mergeable and testable before the key exists, and means adding the key to .env
is the only step needed to switch it on.

The base URL is likewise obtained at signup, not a fixed, guessable value — the
docs say plainly "The URL ... will have been supplied to you when you signed up
and were given your API key." It is therefore config, `MET_OFFICE_NSWWS_BASE_URL`,
not a module constant, and fetch_warnings degrades the same way if it's missing.

Field names and response shape are confirmed against the real "Issued" endpoint
docs (metoffice.github.io/nswws-public-api/issued.html — unreachable from this
development environment's network policy, pasted in by the user instead):
warningId, warningLevel, warningStatus, warningHeadline, issuedDate,
validFromDate, validToDate, warningImpact, warningLikelihood, weatherType,
geometry as MultiPolygon with [lon, lat] coordinates. `weatherType` is a list
of strings (e.g. `["THUNDERSTORM"]`), not a single string. warningStatus is
`ISSUED` | `CANCELLED` | `EXPIRED`, but the server already excludes cancelled
and expired warnings from this endpoint's response — `_DEAD_STATUSES` below is
a defensive backstop, not load-bearing. warningImpact/warningLikelihood are
confirmed integers; the docs state warnings are ranked by warningLevel, then
warningImpact, then warningLikelihood (which `sort_warnings` follows exactly),
and an independently-found metoffice.gov.uk page describing impact as very
low/low/medium/high corroborates higher = more severe, though the exact
integer-to-label mapping is still unconfirmed.

The GeoJSON URL is not a fixed endpoint, confirmed against the real "Atom feed"
docs (metoffice.github.io/nswws-public-api/atom-feed.html — unreachable from
here, again pasted in by the user). `fetch_warnings` is a genuine two-step
fetch: GET `{base_url}/v1.0/objects/feed` for the Atom feed, read the *feed-level*
`<link rel="related">` element's `href` (the "Latest version of all issued
warnings" URL, distinct from any `<entry>`'s own `rel="alternate"` link, which
describes a single past change rather than the current full set), then GET
that URL for the actual GeoJSON. The related URL rotates on every feed update —
the docs explicitly warn that a cached one goes stale and 404s, so the feed
must be re-fetched every poll rather than skipped once the URL is known once.
That is two Met Office requests per 120s poll cycle rather than one, still
within the docs' own "poll every 1-2 minutes" guidance.
"""

import xml.etree.ElementTree as ElementTree

import httpx

from services.geo import point_in_geometry

_ATOM_NS = "{http://www.w3.org/2005/Atom}"

# The server already excludes CANCELLED and EXPIRED warnings from the Issued
# endpoint's response (confirmed in the docs), so this is a defensive backstop
# against a future schema change, not something the real feed is expected to
# ever need. Comparison is case-insensitive; the confirmed literals are
# uppercase ("CANCELLED", "EXPIRED").
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
        weather_types = properties.get("weatherType", [])

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
                # A list per the real API (e.g. ["THUNDERSTORM"]), never a bare
                # string — a non-list value here is defended against rather than
                # trusted, since it would otherwise iterate character-by-character.
                "weather_types": weather_types if isinstance(weather_types, list) else [],
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


def parse_feed_related_url(feed_xml: str) -> str | None:
    """Extract the "latest issued warnings" GeoJSON URL from an NSWWS Atom feed.

    This is the feed-level `<link rel="related">` element — a direct child of
    `<feed>`, not of any `<entry>`. `ElementTree.findall` with a plain tag name
    only matches direct children, which is what keeps this from ever picking up
    an `<entry>`'s own `rel="alternate"` link (a single past change, not the
    current full set) by mistake.

    Returns None on anything unusable — malformed XML, or a well-formed feed
    with no matching link — so a bad or unexpected response degrades to no
    warnings for this poll rather than raising out of the poll loop.
    """
    try:
        root = ElementTree.fromstring(feed_xml)
    except ElementTree.ParseError:
        return None

    for link in root.findall(f"{_ATOM_NS}link"):
        if link.get("rel") == "related":
            return link.get("href")

    return None


async def fetch_warnings(client: httpx.AsyncClient, api_key: str, base_url: str) -> list[dict]:
    """Fetch live UK severe weather warnings from NSWWS.

    Returns an empty list if no API key or base URL is configured — both are
    obtained at signup (see module docstring), not guessable.

    A genuine two-step fetch: the Atom feed for the current "latest issued
    warnings" URL, then that URL for the actual GeoJSON. The feed must be
    re-fetched every call rather than cached, because the URL it returns
    rotates and a stale one 404s.
    """
    if not api_key or not base_url:
        return []

    headers = {"x-api-key": api_key}

    feed_resp = await client.get(f"{base_url}/v1.0/objects/feed", headers=headers)
    feed_resp.raise_for_status()

    warnings_url = parse_feed_related_url(feed_resp.text)
    if warnings_url is None:
        return []

    resp = await client.get(warnings_url, headers=headers)
    resp.raise_for_status()
    return parse_warnings(resp.json())
