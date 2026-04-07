"""Dog walk route router — recommends a walk on non-dog-daycare days."""

import json
import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter

from config import settings
from services.dog_walk import is_dog_daycare_day, load_walk_routes, rank_routes, score_conditions

router = APIRouter(prefix="/api/dog-walk", tags=["dog-walk"])

OPEN_METEO_BASE = "https://api.open-meteo.com/v1"

# Path to walk routes config — overridable in tests
WALK_ROUTES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "walk-routes.json"
)

# Muddiness thresholds — configurable via environment variables
_PRECIP_THRESHOLD_MM = float(os.getenv("WALK_MUDDY_PRECIP_MM", "10.0"))
_SOIL_THRESHOLD = float(os.getenv("WALK_MUDDY_SOIL_MOISTURE", "0.3"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_today_weekday() -> str:
    """Return today's weekday name in lowercase (e.g. 'monday')."""
    return datetime.now(tz=timezone.utc).strftime("%A").lower()


async def fetch_conditions(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    """Fetch soil moisture and recent precipitation from Open-Meteo.

    Returns dict with keys: precip_mm, soil_moisture, available.
    On any HTTP or parsing error, returns available=False.
    """
    try:
        resp = await client.get(
            f"{OPEN_METEO_BASE}/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "precipitation,soil_moisture_0_to_1cm",
                "past_days": 1,
                "forecast_days": 1,
                "timezone": "Europe/London",
            },
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return {"precip_mm": 0.0, "soil_moisture": 0.0, "available": False}

    hourly = data.get("hourly", {})
    times: list[str] = hourly.get("time", [])
    precip_values: list[float] = hourly.get("precipitation", [])
    soil_values: list[float] = hourly.get("soil_moisture_0_to_1cm", [])

    now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:00")
    try:
        current_idx = times.index(now_str)
    except ValueError:
        current_idx = len(times)

    # Sum precipitation for the past 24 hours up to (not including) current hour
    start_idx = max(0, current_idx - 24)
    past_precip = precip_values[start_idx:current_idx]
    precip_mm = sum(v for v in past_precip if v is not None)

    # Current soil moisture
    soil_moisture = 0.0
    if soil_values and current_idx < len(soil_values):
        val = soil_values[current_idx]
        soil_moisture = val if val is not None else 0.0

    return {"precip_mm": precip_mm, "soil_moisture": soil_moisture, "available": True}


def _load_schedule() -> dict:
    schedule_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "commute-schedule.json"
    )
    with open(schedule_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("")
async def get_dog_walk():
    schedule = _load_schedule()
    weekday = get_today_weekday()

    if is_dog_daycare_day(weekday, schedule):
        return {"eligible": False, "conditions": None, "routes": []}

    routes = load_walk_routes(WALK_ROUTES_PATH)

    async with httpx.AsyncClient() as http:
        conditions_data = await fetch_conditions(http, settings.home_lat, settings.home_lon)

    if not conditions_data["available"]:
        conditions = "Unknown"
    else:
        conditions = score_conditions(
            precip_mm=conditions_data["precip_mm"],
            soil_moisture=conditions_data["soil_moisture"],
            precip_threshold=_PRECIP_THRESHOLD_MM,
            soil_threshold=_SOIL_THRESHOLD,
        )

    ranked = rank_routes(routes, conditions)

    return {
        "eligible": True,
        "conditions": conditions,
        "routes": ranked,
    }
