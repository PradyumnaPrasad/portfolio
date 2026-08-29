from fastapi.testclient import TestClient

from app.main import app
from app.world import build_world

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_home_renders_game_and_text_fallback():
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert 'id="stage"' in body
    assert 'id="world-data"' in body
    assert "Dual Insight Engine" in body
    assert "Hexango" in body
    assert "MIT National Hackathon" in body


def test_world_is_consistent():
    w = build_world()
    assert w["rows"] == len(w["terrain"])
    assert all(len(row) == w["cols"] for row in w["terrain"])

    def solid(x, y):
        t = w["terrain"][y][x]
        return (
            t in ("T", "~")
            or [x, y] in w["trees"]
            or any(s["x"] == x and s["y"] == y for s in w["structures"])
        )

    # every door mat and the pad and the start must be on a walkable tile
    for s in w["structures"]:
        mx, my = s["x"], s["y"] + 1
        assert not solid(mx, my), f"{s['name']} door blocked at {mx},{my}"
    assert not solid(w["pad"]["x"], w["pad"]["y"])
    assert not solid(w["start"]["x"], w["start"]["y"])

    # no two structures share a tile
    tiles = [(s["x"], s["y"]) for s in w["structures"]]
    assert len(tiles) == len(set(tiles))


def test_api_world():
    r = client.get("/api/world")
    assert r.status_code == 200
    assert r.json()["structures"]


def test_robots():
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert "User-agent" in r.text
