"""Weather router — Open-Meteo integration (no API key required)."""

import os
from datetime import datetime, timedelta

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


_SUN_CODES = frozenset({0, 1})

# Anything falling out of the sky — drizzle, rain, snow, showers, thunder. The
# glyph only has to answer "do I need a coat" at a glance, so they share one mark.
_RAIN_CODES = frozenset(
    {51, 53, 55, 61, 63, 65, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99}
)


def map_weather_icon(code: int) -> str:
    """Map a WMO weather code to one of the three glyphs the cards can draw.

    Unrecognised codes fall back to the neutral cloud rather than guessing.
    """
    if code in _SUN_CODES:
        return "sun"
    if code in _RAIN_CODES:
        return "rain"
    return "cloud"


def parse_current(current_data: dict) -> dict:
    """Extract current conditions from an Open-Meteo current block."""
    return {
        "temperature_celsius": current_data.get("temperature_2m"),
        "apparent_temperature_celsius": current_data.get("apparent_temperature"),
        "weather_description": map_weather_code(current_data.get("weather_code", 0)),
        "wind_speed_kmh": current_data.get("wind_speed_10m"),
        "humidity_percent": current_data.get("relative_humidity_2m"),
    }


def parse_daily_high(daily_data: dict, day_index: int = 0) -> float | None:
    """Return a day's maximum temperature from an Open-Meteo daily block."""
    temps = daily_data.get("temperature_2m_max", [])
    return temps[day_index] if len(temps) > day_index else None


def parse_daily_rainfall(daily_data: dict, day_index: int = 0) -> dict:
    """Return a day's total precipitation (mm) and max probability (%) from an Open-Meteo daily block."""
    totals = daily_data.get("precipitation_sum", [])
    probs = daily_data.get("precipitation_probability_max", [])
    return {
        "total_mm": totals[day_index] if len(totals) > day_index else None,
        "probability_percent": probs[day_index] if len(probs) > day_index else None,
    }


def parse_daily_description(daily_data: dict, day_index: int = 0) -> str | None:
    """Return a day's aggregate weather description from an Open-Meteo daily block.

    None means the data is absent; "Unknown" means the code itself is unrecognised.
    The distinction matters — the card hides the line for the former and shows it
    for the latter.
    """
    codes = daily_data.get("weather_code", [])
    if len(codes) <= day_index:
        return None
    return map_weather_code(codes[day_index])


def resolve_day_offset(hourly_data: dict, day_index: int = 0) -> int:
    """Index of the first hourly entry falling on the day_index-th local day.

    Open-Meteo aligns hourly arrays to LOCAL days, so a day is not always 24
    entries long: with timezone=Europe/London the clocks-back day has 25 and the
    clocks-forward day has 23. Deriving the offset from the timestamps rather
    than assuming 24 keeps tomorrow's windows correct across both.

    Falls back to whole days when the response carries no time list.
    """
    if day_index == 0:
        return 0
    starts = _day_start_indices(hourly_data)
    if len(starts) > day_index:
        return starts[day_index]
    return day_index * 24


def _day_start_indices(hourly_data: dict) -> list[int]:
    """Index at which each local day begins, derived from the hourly timestamps.

    Returns an empty list when the response carries no time list.
    """
    times = hourly_data.get("time", [])
    if not times:
        return []
    starts = [0]
    for index in range(1, len(times)):
        if times[index][:10] != times[index - 1][:10]:
            starts.append(index)
    return starts


def parse_rain_windows(
    hourly_data: dict, threshold: int = 50, day_index: int = 0
) -> list[dict]:
    """Return contiguous hour windows where precipitation probability meets the threshold.

    Each window is {start_hour, end_hour} where end_hour is exclusive, and both are
    hours of the requested local day — so the frontend formats tomorrow's windows
    with exactly the same code as today's.
    """
    all_probs = hourly_data.get("precipitation_probability", [])
    start_index = resolve_day_offset(hourly_data, day_index)
    starts = _day_start_indices(hourly_data)
    if len(starts) > day_index + 1:
        end_index = starts[day_index + 1]
    elif starts:
        end_index = len(all_probs)
    else:
        end_index = start_index + 24
    probs = all_probs[start_index:end_index]
    windows = []
    start = None
    for hour, prob in enumerate(probs):
        if prob is not None and prob >= threshold:
            if start is None:
                start = hour
        else:
            if start is not None:
                windows.append({"start_hour": start, "end_hour": hour})
                start = None
    if start is not None:
        windows.append({"start_hour": start, "end_hour": len(probs)})
    return windows


def parse_location_name(address: dict) -> str:
    """Extract the most specific useful place name from a Nominatim address dict."""
    return (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("county")
        or ""
    )


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
            locations.append({"name": label, "lat": lat, "lon": lon, "geocode": mode == "office"})

    return locations


def resolve_tomorrow_weekday(now: datetime) -> str:
    """Return tomorrow's weekday as a lowercase schedule key."""
    return (now + timedelta(days=1)).strftime("%A").lower()


def resolve_fetch_targets(today: list[dict], tomorrow: list[dict]) -> list[dict]:
    """Union both days' locations into one fetch target per unique coordinate.

    Open-Meteo returns both days from a single request, so a coordinate wanted by
    either day is fetched exactly once. On the common day — where tomorrow's
    commute modes match today's — this costs no extra calls at all.

    A target is marked for geocoding if EITHER day wants it geocoded: the same
    coordinate can be an office tomorrow and home today.
    """
    targets: list[dict] = []
    by_coord: dict[tuple[float, float], dict] = {}

    for loc in [*today, *tomorrow]:
        key = (loc["lat"], loc["lon"])
        existing = by_coord.get(key)
        if existing is None:
            target = {"lat": loc["lat"], "lon": loc["lon"], "geocode": loc["geocode"]}
            by_coord[key] = target
            targets.append(target)
        elif loc["geocode"]:
            existing["geocode"] = True

    return targets


# Module-level cache for geocoded names — coordinates are fixed per session
_geocode_cache: dict[tuple[float, float], str] = {}

NOMINATIM_BASE = "https://nominatim.openstreetmap.org"


async def fetch_location_name(client: httpx.AsyncClient, lat: float, lon: float) -> str:
    """Reverse-geocode coordinates to a city/town name via Nominatim.

    Returns an empty string if the request fails or no useful name is found.
    """
    key = (lat, lon)
    if key in _geocode_cache:
        return _geocode_cache[key]

    try:
        resp = await client.get(
            f"{NOMINATIM_BASE}/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "FamilyDashboard/1.0 (personal home dashboard)"},
        )
        resp.raise_for_status()
        name = parse_location_name(resp.json().get("address", {}))
    except Exception:
        name = ""

    _geocode_cache[key] = name
    return name


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
            "daily": "temperature_2m_max,precipitation_sum,precipitation_probability_max,weather_code",
            "hourly": "precipitation_probability",
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
    from scheduler import is_within_weather_poll_window as _scheduler_in_window

    is_stale = not _scheduler_in_window(_get_now())
    if _cache is None:
        return {"locations": [], "is_stale": is_stale}
    return {**_cache, "is_stale": is_stale}


def _build_today_entry(name: str, data: dict) -> dict:
    """Assemble today's card entry — live conditions plus the day's aggregates."""
    daily = data.get("daily", {})
    current_raw = data.get("current", {})
    return {
        "name": name,
        "icon": map_weather_icon(current_raw.get("weather_code", 0)),
        "current": parse_current(current_raw),
        "daily_high_celsius": parse_daily_high(daily, 0),
        "daily_rainfall": parse_daily_rainfall(daily, 0),
        "rain_windows": parse_rain_windows(data.get("hourly", {}), day_index=0),
    }


def _build_tomorrow_entry(name: str, data: dict) -> dict:
    """Assemble tomorrow's card entry.

    Deliberately carries no "current" block — a future day has no current
    conditions, and offering one would invite a card that renders a fake "now".
    """
    daily = data.get("daily", {})
    codes = daily.get("weather_code", [])
    return {
        "name": name,
        "icon": map_weather_icon(codes[1]) if len(codes) > 1 else "cloud",
        "weather_description": parse_daily_description(daily, 1),
        "daily_high_celsius": parse_daily_high(daily, 1),
        "daily_rainfall": parse_daily_rainfall(daily, 1),
        "rain_windows": parse_rain_windows(data.get("hourly", {}), day_index=1),
    }


async def fetch_weather_data() -> dict:
    """Fetch live weather data per active destination. Called by the scheduler."""
    schedule = load_schedule(_SCHEDULE_PATH)
    now = _get_now()
    today_weekday = now.strftime("%A").lower()
    tomorrow_weekday = resolve_tomorrow_weekday(now)

    today_locations = resolve_weather_locations(schedule, today_weekday, settings)
    tomorrow_locations = resolve_weather_locations(schedule, tomorrow_weekday, settings)
    targets = resolve_fetch_targets(today_locations, tomorrow_locations)

    async with httpx.AsyncClient() as http:
        by_coord: dict[tuple[float, float], dict] = {}
        names_by_coord: dict[tuple[float, float], str] = {}

        for target in targets:
            key = (target["lat"], target["lon"])
            by_coord[key] = await fetch_weather(http, target["lat"], target["lon"])
            if target["geocode"]:
                city = await fetch_location_name(http, target["lat"], target["lon"])
                if city:
                    names_by_coord[key] = city

        def display_name(loc: dict) -> str:
            key = (loc["lat"], loc["lon"])
            # Only an office location is geocoded; "Home" keeps its own label
            # even when the same coordinate is an office on the other day.
            if loc["geocode"]:
                return names_by_coord.get(key, loc["name"])
            return loc["name"]

        result_locations = [
            _build_today_entry(display_name(loc), by_coord[(loc["lat"], loc["lon"])])
            for loc in today_locations
        ]
        tomorrow_entries = [
            _build_tomorrow_entry(display_name(loc), by_coord[(loc["lat"], loc["lon"])])
            for loc in tomorrow_locations
        ]

    return {
        "locations": result_locations,
        "tomorrow": {
            "weekday": tomorrow_weekday.capitalize(),
            "locations": tomorrow_entries,
        },
    }
