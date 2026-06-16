from unittest.mock import patch

from fastapi.testclient import TestClient

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
