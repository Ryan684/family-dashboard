"""Commute schedule resolver — loads config and resolves per-commuter day state."""

import json


def load_schedule(path: str) -> dict:
    """Load and return the commute schedule config from a JSON file."""
    with open(path) as f:
        return json.load(f)


def resolve_commuter_day(commuter: dict, weekday: str, schedule: dict) -> dict:
    """Resolve a commuter's mode and active drops for the given weekday.

    Applies nursery and dog gate rules:
    - Nursery drop only occurs when today is in nursery.days AND commuter
      has nursery_drop=True in their schedule.
    - Dog drop only occurs when today is in dog_daycare.days AND commuter
      matches weekly_dropper.

    Drop order follows commuter's drop_order config.

    Returns dict with keys: mode, drops.
    """
    day_config = commuter["schedule"].get(weekday, {"mode": "off", "nursery_drop": False})
    mode = day_config["mode"]

    nursery_days = schedule["nursery"]["days"]
    dog_days = schedule["dog_daycare"]["days"]
    weekly_dropper = schedule["dog_daycare"]["weekly_dropper"]

    active_drops: set[str] = set()

    if day_config.get("nursery_drop") and weekday in nursery_days:
        active_drops.add("nursery")

    if weekday in dog_days and commuter["name"] == weekly_dropper:
        active_drops.add("dog")

    # Apply drop_order to produce a deterministic ordered list
    drops = [d for d in commuter.get("drop_order", []) if d in active_drops]

    return {"mode": mode, "drops": drops}


def build_waypoints(
    mode: str,
    drops: list[str],
    home: tuple[float, float],
    work: tuple[float, float],
    nursery: tuple[float, float],
    dog_daycare: tuple[float, float],
) -> list[tuple[float, float]]:
    """Build an ordered waypoint list for a TomTom calculateRoute call.

    office + no drops  → [home, work]
    office + drops     → [home, ...drops..., work]
    wfh/off + no drops → []  (commuter omitted — no route needed)
    wfh/off + drops    → [home, ...drops..., home]
    """
    if not drops and mode != "office":
        return []

    drop_coords = {"nursery": nursery, "dog": dog_daycare}
    middle = [drop_coords[d] for d in drops]

    if mode == "office":
        return [home] + middle + [work]
    # wfh or off with drops → out-and-back
    return [home] + middle + [home]
