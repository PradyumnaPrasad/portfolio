from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_home_renders_key_content():
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert "Pradyumna Prasad" in body
    assert "Dual Insight Engine" in body
    assert "Hexango" in body


def test_stats_counts_views():
    client.get("/")
    r = client.get("/stats")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_robots():
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert "User-agent" in r.text
