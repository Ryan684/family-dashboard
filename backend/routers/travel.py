"""Travel router — TomTom Routing and Traffic Incident API integration."""

import re
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter

from config import settings

router = APIRouter(prefix="/api/travel", tags=["travel"])

TOMTOM_BASE = "https://api.tomtom.com"

# Module-level cache: holds last successful response dict
_cache: dict | None = None


def _get_now() -> datetime:
    return datetime.now()


# ---------------------------------------------------------------------------
# Pure logic functions
# ---------------------------------------------------------------------------


def classify_delay(delay_seconds: int, no_traffic_time_seconds: int) -> str:
    """Return green / amber / red based on delay as a fraction of free-flow time."""
    if no_traffic_time_seconds == 0:
        return "green"
    ratio = delay_seconds / no_traffic_time_seconds
    if ratio < 0.10:
        return "green"
    if ratio <= 0.25:
        return "amber"
    return "red"


def extract_road_names(instructions: list[dict]) -> list[str]:
    """Return up to 3 unique motorway and A-road names from guidance instructions."""
    seen: list[str] = []
    for inst in instructions:
        road = inst.get("roadName") or ""
        if road and re.match(r"^[AM]\d", road) and road not in seen:
            seen.append(road)
            if len(seen) == 3:
                break
    return seen


def format_route_description(road_names: list[str]) -> str:
    """Format road names as 'via X and Y' or 'via X, Y and Z'."""
    if not road_names:
        return ""
    if len(road_names) == 1:
        return f"via {road_names[0]}"
    return "via " + ", ".join(road_names[:-1]) + " and " + road_names[-1]


def calculate_bounding_box(points: list[dict]) -> dict:
    """Return min/max lat/lon bounding box from a list of coordinate dicts."""
    lats = [p["latitude"] for p in points]
    lons = [p["longitude"] for p in points]
    return {
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lon": min(lons),
        "max_lon": max(lons),
    }


def expand_bounding_box(bbox: dict, degrees: float = 0.02) -> dict:
    """Expand a bounding box by a fixed number of degrees in all directions."""
    return {
        "min_lat": bbox["min_lat"] - degrees,
        "max_lat": bbox["max_lat"] + degrees,
        "min_lon": bbox["min_lon"] - degrees,
        "max_lon": bbox["max_lon"] + degrees,
    }


def is_within_poll_window(now: datetime, start, end) -> bool:
    """Return True if now.time() falls within [start, end] inclusive."""
    current = now.time()
    return start <= current <= end


def parse_incidents(raw_incidents: list[dict]) -> list[dict]:
    """Filter and normalise TomTom incident objects. Excludes minor (<=1) incidents."""
    result = []
    for incident in raw_incidents:
        props = incident.get("properties", {})
        magnitude = props.get("magnitudeOfDelay", 0)
        if magnitude < 2:
            continue
        events = props.get("events", [])
        description = events[0].get("description", "") if events else ""
        road_numbers = props.get("roadNumbers") or []
        road = road_numbers[0] if road_numbers else props.get("from", "")
        result.append(
            {
                "type": props.get("iconCategory", "UNKNOWN"),
                "description": description,
                "road": road,
            }
        )
    return result


# ---------------------------------------------------------------------------
# Route building from TomTom response
# ---------------------------------------------------------------------------


def _collect_points(route: dict) -> list[dict]:
    points: list[dict] = []
    for leg in route.get("legs", []):
        points.extend(leg.get("points", []))
    return points


def _collect_instructions(route: dict) -> list[dict]:
    instructions: list[dict] = []
    for leg in route.get("legs", []):
        guidance = leg.get("guidance", {})
        instructions.extend(guidance.get("instructions", []))
    return instructions


def _build_route_option(route: dict) -> dict:
    summary = route["summary"]
    travel_time = summary["travelTimeInSeconds"]
    no_traffic_time = summary["noTrafficTravelTimeInSeconds"]
    delay = summary.get("trafficDelayInSeconds", max(0, travel_time - no_traffic_time))

    road_names = extract_road_names(_collect_instructions(route))
    description = format_route_description(road_names)

    return {
        "travel_time_seconds": travel_time,
        "delay_seconds": delay,
        "distance_meters": summary["lengthInMeters"],
        "description": description,
        "delay_colour": classify_delay(delay, no_traffic_time),
    }


def _build_all_points(routes_response: dict) -> list[dict]:
    points: list[dict] = []
    for route in routes_response.get("routes", []):
        points.extend(_collect_points(route))
    return points


def _extract_traffic_model_id(routes_response: dict) -> str:
    routes = routes_response.get("routes", [])
    if not routes:
        return ""
    return routes[0].get("summary", {}).get("trafficModelId", "")


# ---------------------------------------------------------------------------
# TomTom HTTP calls
# ---------------------------------------------------------------------------


async def fetch_routes(
    client: httpx.AsyncClient,
    origin: tuple[float, float],
    destination: tuple[float, float],
    api_key: str,
) -> dict:
    origin_str = f"{origin[0]},{origin[1]}"
    dest_str = f"{destination[0]},{destination[1]}"
    url = f"{TOMTOM_BASE}/routing/1/calculateRoute/{origin_str}:{dest_str}/json"
    resp = await client.get(
        url,
        params={"maxAlternatives": 1, "traffic": "true", "key": api_key},
    )
    resp.raise_for_status()
    return resp.json()


async def fetch_incidents(
    client: httpx.AsyncClient,
    bbox: dict,
    traffic_model_id: str,
    api_key: str,
) -> list[dict]:
    bbox_str = (
        f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
    )
    params: dict[str, Any] = {
        "key": api_key,
        "bbox": bbox_str,
        "fields": "{incidents{type,properties{iconCategory,magnitudeOfDelay,events{description},from,roadNumbers}}}",
        "language": "en-US",
        "categoryFilter": "0,1,2,3,4,5,6,7,8,9,10,11,12,13,14",
        "timeValidityFilter": "present",
    }
    if traffic_model_id:
        params["modelId"] = traffic_model_id
    resp = await client.get(
        f"{TOMTOM_BASE}/traffic/services/5/incidentDetails",
        params=params,
    )
    resp.raise_for_status()
    return resp.json().get("incidents", [])


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("")
async def get_travel():
    from scheduler import is_within_poll_window as _scheduler_in_window

    is_stale = not _scheduler_in_window(_get_now())
    if _cache is None:
        return {
            "home_to_work": [],
            "home_to_nursery": [],
            "incidents": [],
            "is_stale": is_stale,
        }
    return {**_cache, "is_stale": is_stale}


async def fetch_travel_data() -> dict:
    """Fetch live travel data from TomTom. Called by the scheduler."""
    home = (settings.home_lat, settings.home_lon)
    work = (settings.work_lat, settings.work_lon)
    nursery = (settings.nursery_lat, settings.nursery_lon)

    async with httpx.AsyncClient() as http:
        work_routes_raw, nursery_routes_raw = (
            await fetch_routes(http, home, work, settings.tomtom_api_key),
            await fetch_routes(http, home, nursery, settings.tomtom_api_key),
        )

        all_points = _build_all_points(work_routes_raw) + _build_all_points(
            nursery_routes_raw
        )
        bbox = expand_bounding_box(calculate_bounding_box(all_points))
        traffic_model_id = _extract_traffic_model_id(work_routes_raw)

        raw_incidents = await fetch_incidents(
            http, bbox, traffic_model_id, settings.tomtom_api_key
        )

    return {
        "home_to_work": [
            _build_route_option(r) for r in work_routes_raw.get("routes", [])
        ],
        "home_to_nursery": [
            _build_route_option(r) for r in nursery_routes_raw.get("routes", [])
        ],
        "incidents": parse_incidents(raw_incidents),
    }
