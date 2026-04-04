"""Weather router — Open-Meteo integration (no API key required)."""

import httpx
from fastapi import APIRouter

from config import settings

router = APIRouter(prefix="/api/weather", tags=["weather"])

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


def find_current_hour_index(hourly_times: list[str], current_time: str) -> int:
    """Return the index of current_time in hourly_times, or 0 if not found."""
    try:
        return hourly_times.index(current_time)
    except ValueError:
        return 0


def parse_forecast(hourly_data: dict, start_index: int, count: int = 6) -> list[dict]:
    """Return `count` hourly forecast entries starting from start_index."""
    times = hourly_data.get("time", [])
    temps = hourly_data.get("temperature_2m", [])
    codes = hourly_data.get("weather_code", [])
    precip = hourly_data.get("precipitation_probability", [])
    result = []
    for i in range(start_index, min(start_index + count, len(times))):
        result.append(
            {
                "time": times[i],
                "temperature_celsius": temps[i] if i < len(temps) else None,
                "weather_description": map_weather_code(
                    codes[i] if i < len(codes) else 0
                ),
                "precipitation_probability": precip[i] if i < len(precip) else 0,
            }
        )
    return result


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
            "hourly": "temperature_2m,weather_code,precipitation_probability",
            "forecast_days": 2,
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
    async with httpx.AsyncClient() as http:
        data = await fetch_weather(http, settings.home_lat, settings.home_lon)

    current_raw = data.get("current", {})
    current = parse_current(current_raw)

    hourly = data.get("hourly", {})
    start_idx = find_current_hour_index(
        hourly.get("time", []), current_raw.get("time", "")
    )
    forecast = parse_forecast(hourly, start_idx)

    return {"current": current, "forecast": forecast}
