import os
from datetime import time

from dotenv import load_dotenv

load_dotenv()


def _parse_time(value: str, default: str) -> time:
    raw = value or default
    hour, minute = raw.split(":")
    return time(int(hour), int(minute))


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise ValueError(f"{name} is required but not set in the environment")
    return val


class Settings:
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    here_api_key: str = os.getenv("HERE_API_KEY", "")
    # Optional, deliberately: _require_env raises at import time, and deploy.sh
    # never touches .env, so a required key would take the backend down at the
    # next nightly deploy. Absent key simply means no warnings banner.
    met_office_nswws_api_key: str = os.getenv("MET_OFFICE_NSWWS_API_KEY", "")
    # The API base URL is issued alongside the key at signup, not a fixed or
    # guessable value — also optional, for the same reason as the key above.
    met_office_nswws_base_url: str = os.getenv("MET_OFFICE_NSWWS_BASE_URL", "")

    home_lat: float = float(os.getenv("HOME_LAT", "0"))
    home_lon: float = float(os.getenv("HOME_LON", "0"))
    commuter_1_work_lat: float = float(os.getenv("COMMUTER_1_WORK_LAT", "0"))
    commuter_1_work_lon: float = float(os.getenv("COMMUTER_1_WORK_LON", "0"))
    commuter_2_work_lat: float = float(os.getenv("COMMUTER_2_WORK_LAT", "0"))
    commuter_2_work_lon: float = float(os.getenv("COMMUTER_2_WORK_LON", "0"))
    nursery_lat: float = float(os.getenv("NURSERY_LAT", "0"))
    nursery_lon: float = float(os.getenv("NURSERY_LON", "0"))
    dog_daycare_lat: float = float(os.getenv("DOG_DAYCARE_LAT", "0"))
    dog_daycare_lon: float = float(os.getenv("DOG_DAYCARE_LON", "0"))

    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "120"))
    poll_window_start: time = _parse_time(
        os.getenv("POLL_WINDOW_START", ""), "06:30"
    )
    poll_window_end: time = _parse_time(os.getenv("POLL_WINDOW_END", ""), "09:30")
    weather_poll_window_end: time = _parse_time(_require_env("WEATHER_POLL_WINDOW_END"), "")
    calendar_poll_interval_seconds: int = int(_require_env("CALENDAR_POLL_INTERVAL_SECONDS"))

    apple_caldav_url: str = os.getenv("APPLE_CALDAV_URL", "https://caldav.icloud.com")
    apple_caldav_username: str = os.getenv("APPLE_CALDAV_USERNAME", "")
    apple_caldav_password: str = os.getenv("APPLE_CALDAV_PASSWORD", "")
    apple_caldav_calendar_name: str = os.getenv("APPLE_CALDAV_CALENDAR_NAME", "Family")


settings = Settings()
