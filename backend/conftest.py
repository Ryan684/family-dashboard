import os


def pytest_configure(config):
    """Set required env vars before any test module is imported."""
    os.environ.setdefault("WEATHER_POLL_WINDOW_END", "22:00")
    os.environ.setdefault("CALENDAR_POLL_INTERVAL_SECONDS", "1800")
