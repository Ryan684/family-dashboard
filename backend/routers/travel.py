"""Travel router — per-commuter dynamic routing via TomTom Routing and Incidents APIs."""

import os
import re
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter

from config import settings
from services.commute_schedule import build_waypoints, load_schedule, resolve_commuter_day

router = APIRouter(prefix="/api/travel", tags=["travel"])

TOMTOM_BASE = "https://api.tomtom.com"
_SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "commute-schedule.json")

# Module-level cache: holds last successful response dict
_cache: dict | None = None


def _get_now() -> datetime:
    return datetime.now()


def _get_weekday() -> str:
    return _get_now().strftime("%A").lower()


# ---------------------------------------------------------------------------
# Pure logic functions (unchanged)
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
# Config helpers (injectable for testing)
# ---------------------------------------------------------------------------


def get_coords() -> dict:
    """Return coordinate lookup dict built from settings."""
    home = (settings.home_lat, settings.home_lon)
    return {
        "home": home,
        "work": {
            # Keyed by commuter index; matched to schedule commuters[] by position
            "Commuter1": (settings.commuter_1_work_lat, settings.commuter_1_work_lon),
            "Commuter2": (settings.commuter_2_work_lat, settings.commuter_2_work_lon),
        },
        "nursery": (settings.nursery_lat, settings.nursery_lon),
        "dog_daycare": (settings.dog_daycare_lat, settings.dog_daycare_lon),
    }


# ---------------------------------------------------------------------------
# TomTom HTTP calls
# ---------------------------------------------------------------------------


async def fetch_routes(
    client: httpx.AsyncClient,
    waypoints: list[tuple[float, float]],
    api_key: str,
) -> dict:
    """Fetch routes for an ordered list of waypoints (origin + optional stops + dest)."""
    locations = ":".join(f"{lat},{lon}" for lat, lon in waypoints)
    url = f"{TOMTOM_BASE}/routing/1/calculateRoute/{locations}/json"
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
        return {"commuters": [], "is_stale": is_stale}
    return {**_cache, "is_stale": is_stale}


async def fetch_travel_data() -> dict:
    """Fetch live travel data for all active commuters. Called by the scheduler."""
    schedule = load_schedule(_SCHEDULE_PATH)
    coords = get_coords()
    weekday = _get_weekday()

    # Build per-commuter work coord lookup by name
    work_by_name = {
        c["name"]: coords["work"].get(c["name"], coords["work"].get("Commuter1"))
        for c in schedule["commuters"]
    }
    # Fall back: map by position for names not matching the hardcoded keys
    for i, commuter in enumerate(schedule["commuters"]):
        key = f"Commuter{i + 1}"
        if commuter["name"] not in coords["work"] and key in coords["work"]:
            work_by_name[commuter["name"]] = coords["work"][key]

    commuter_results = []

    async with httpx.AsyncClient() as http:
        all_route_points: list[dict] = []
        all_traffic_model_ids: list[str] = []
        commuter_routes_raw: list[tuple[dict, dict]] = []  # (commuter, routes_response)

        for commuter in schedule["commuters"]:
            day = resolve_commuter_day(commuter, weekday, schedule)
            waypoints = build_waypoints(
                mode=day["mode"],
                drops=day["drops"],
                home=coords["home"],
                work=work_by_name[commuter["name"]],
                nursery=coords["nursery"],
                dog_daycare=coords["dog_daycare"],
            )

            if not waypoints:
                # WFH or off with no drops — omit commuter entirely
                continue

            routes_raw = await fetch_routes(http, waypoints, settings.tomtom_api_key)
            all_route_points.extend(_build_all_points(routes_raw))
            all_traffic_model_ids.append(_extract_traffic_model_id(routes_raw))
            commuter_routes_raw.append((commuter, day, routes_raw))

        if not commuter_routes_raw:
            return {"commuters": []}

        # Fetch incidents once covering all active routes
        bbox = expand_bounding_box(calculate_bounding_box(all_route_points))
        traffic_model_id = next((t for t in all_traffic_model_ids if t), "")
        raw_incidents = await fetch_incidents(
            http, bbox, traffic_model_id, settings.tomtom_api_key
        )

    incidents = parse_incidents(raw_incidents)

    for commuter, day, routes_raw in commuter_routes_raw:
        commuter_results.append(
            {
                "name": commuter["name"],
                "mode": day["mode"],
                "drops": day["drops"],
                "routes": [_build_route_option(r) for r in routes_raw.get("routes", [])],
                "incidents": incidents,
            }
        )

    return {"commuters": commuter_results}
