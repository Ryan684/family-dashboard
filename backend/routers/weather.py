"""Weather router — Open-Meteo integration (no API key required)."""

import os
from datetime import datetime

import httpx
from fastapi import APIRouter

from config import settings
from services.commute_schedule import load_schedule

router = APIRouter(prefix="/api/weather", tags=["weather"])

# Module-level cache: holds last successful response dict
_cache: dict | None = None

_SCHEDULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "commute-schedule.json"
)


def _get_now() -> datetime:
    return datetime.now()


OPEN_METEO_BASE = "https://api.open-meteo.com/v1"

_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Moderate showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


# ---------------------------------------------------------------------------
# Pure logic functions
# ---------------------------------------------------------------------------


def map_weather_code(code: int) -> str:
    """Map a WMO weather interpretation code to a human-readable description."""
    return _WMO_DESCRIPTIONS.get(code, "Unknown")


def parse_current(current_data: dict) -> dict:
    """Extract current conditions from an Open-Meteo current block."""
    return {
        "temperature_celsius": current_data.get("temperature_2m"),
        "apparent_temperature_celsius": current_data.get("apparent_temperature"),
        "weather_description": map_weather_code(current_data.get("weather_code", 0)),
        "wind_speed_kmh": current_data.get("wind_speed_10m"),
        "humidity_percent": current_data.get("relative_humidity_2m"),
    }


def parse_daily_high(daily_data: dict) -> float | None:
    """Return today's maximum temperature from an Open-Meteo daily block."""
    temps = daily_data.get("temperature_2m_max", [])
    return temps[0] if temps else None


def resolve_weather_locations(schedule: dict, weekday: str, cfg) -> list[dict]:
    """Return unique weather fetch targets based on today's commuter modes.

    Each commuter contributes their end location:
      office → their work coordinates (labelled "{Name}'s Office")
      wfh/off → home coordinates (labelled "Home")

    Locations with identical coordinates are deduplicated so the same place
    is never fetched or displayed twice.
    """
    work_coords = [
        (cfg.commuter_1_work_lat, cfg.commuter_1_work_lon),
        (cfg.commuter_2_work_lat, cfg.commuter_2_work_lon),
    ]
    home = (cfg.home_lat, cfg.home_lon)

    seen: set[tuple[float, float]] = set()
    locations: list[dict] = []

    for i, commuter in enumerate(schedule["commuters"]):
        day_config = commuter["schedule"].get(weekday, {"mode": "off"})
        mode = day_config["mode"]
        name = commuter["name"]

        if mode == "office" and i < len(work_coords):
            lat, lon = work_coords[i]
            label = f"{name}'s Office"
        else:
            lat, lon = home
            label = "Home"

        key = (lat, lon)
        if key not in seen:
            seen.add(key)
            locations.append({"name": label, "lat": lat, "lon": lon})

    return locations


# ---------------------------------------------------------------------------
# Open-Meteo HTTP call
# ---------------------------------------------------------------------------


async def fetch_weather(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    resp = await client.get(
        f"{OPEN_METEO_BASE}/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
            "daily": "temperature_2m_max",
            "forecast_days": 1,
            "wind_speed_unit": "kmh",
            "timezone": "Europe/London",
        },
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("")
async def get_weather():
    from scheduler import is_within_poll_window as _scheduler_in_window

    is_stale = not _scheduler_in_window(_get_now())
    if _cache is None:
        return {"locations": [], "is_stale": is_stale}
    return {**_cache, "is_stale": is_stale}


async def fetch_weather_data() -> dict:
    """Fetch live weather data per active destination. Called by the scheduler."""
    schedule = load_schedule(_SCHEDULE_PATH)
    weekday = _get_now().strftime("%A").lower()
    locations = resolve_weather_locations(schedule, weekday, settings)

    result_locations = []
    async with httpx.AsyncClient() as http:
        for loc in locations:
            data = await fetch_weather(http, loc["lat"], loc["lon"])
            current = parse_current(data.get("current", {}))
            daily_high = parse_daily_high(data.get("daily", {}))
            result_locations.append(
                {
                    "name": loc["name"],
                    "current": current,
                    "daily_high_celsius": daily_high,
                }
            )

    return {"locations": result_locations}
