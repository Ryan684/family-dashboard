"""Dog walk service — pure logic for eligibility, conditions scoring, and route ranking."""

import json


def is_dog_daycare_day(weekday: str, schedule: dict) -> bool:
    """Return True if weekday is a dog daycare day per the schedule."""
    return weekday in schedule.get("dog_daycare", {}).get("days", [])


def score_conditions(
    precip_mm: float,
    soil_moisture: float,
    precip_threshold: float,
    soil_threshold: float,
) -> str:
    """Return a conditions label based on recent precipitation and soil moisture.

    Rules:
      Both exceed threshold → "Very wet"
      Either exceeds threshold → "Wet"
      Neither exceeds threshold → "Dry"
    Boundary values (exactly at threshold) are treated as not exceeding.
    """
    precip_wet = precip_mm > precip_threshold
    soil_wet = soil_moisture > soil_threshold

    if precip_wet and soil_wet:
        return "Very wet"
    if precip_wet or soil_wet:
        return "Wet"
    return "Dry"


def rank_routes(routes: list[dict], conditions: str) -> list[dict]:
    """Annotate each route with a 'suitable' flag and sort suitable first.

    Suitability rules by conditions:
      Dry / Unknown → all routes suitable
      Wet           → mud_sensitivity >= 3 → unsuitable
      Very wet      → mud_sensitivity >= 2 → unsuitable
    """
    if not routes:
        return []

    threshold = {
        "Dry": 999,
        "Unknown": 999,
        "Wet": 3,
        "Very wet": 2,
    }.get(conditions, 999)

    annotated = [
        {**r, "suitable": r.get("mud_sensitivity", 1) < threshold}
        for r in routes
    ]
    # Stable sort: suitable routes first, then unsuitable
    return sorted(annotated, key=lambda r: 0 if r["suitable"] else 1)


def load_walk_routes(path: str) -> list[dict]:
    """Load and return the list of walk routes from a JSON config file."""
    with open(path) as f:
        data = json.load(f)
    return data.get("routes", [])
