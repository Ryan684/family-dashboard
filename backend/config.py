import os
from datetime import time

from dotenv import load_dotenv

load_dotenv()


def _parse_time(value: str, default: str) -> time:
    raw = value or default
    hour, minute = raw.split(":")
    return time(int(hour), int(minute))


class Settings:
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

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


settings = Settings()
