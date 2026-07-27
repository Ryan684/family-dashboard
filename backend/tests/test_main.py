import asyncio
from unittest.mock import patch

from fastapi.testclient import TestClient

import main
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_index_html(tmp_path):
    dist = tmp_path / "frontend" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<html><body>dashboard</body></html>")

    with patch("main.DIST_DIR", dist):
        response = client.get("/")
    assert response.status_code == 200
    assert "dashboard" in response.text


# ---------------------------------------------------------------------------
# Lifespan: the scheduler task is started on startup and cancelled on shutdown.
# TestClient only runs lifespan when used as a context manager.
# ---------------------------------------------------------------------------


def test_lifespan_starts_and_cancels_scheduler():
    events = []

    async def fake_scheduler():
        events.append("started")
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            events.append("cancelled")
            raise

    with patch("main.run_scheduler", fake_scheduler):
        with TestClient(main.app) as c:
            assert c.get("/health").status_code == 200
            assert events == ["started"], events

    assert events == ["started", "cancelled"], events
