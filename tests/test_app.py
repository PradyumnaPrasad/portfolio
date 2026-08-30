from app.world import build_world


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_home_renders_game_and_text_fallback(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert 'id="stage"' in body
    assert 'id="world-data"' in body
    assert "Dual Insight Engine" in body
    assert "Hexango" in body
    assert "MIT National Hackathon" in body


def test_world_is_consistent(client, db):
    w = build_world(db)
    assert w["rows"] == len(w["terrain"])
    assert all(len(row) == w["cols"] for row in w["terrain"])
    assert len(w["structures"]) == 11

    def solid(x, y):
        t = w["terrain"][y][x]
        return (
            t in ("T", "~")
            or [x, y] in w["trees"]
            or any(s["x"] == x and s["y"] == y for s in w["structures"])
        )

    for s in w["structures"]:
        assert not solid(s["x"], s["y"] + 1), f"{s['name']} door blocked"
    assert not solid(w["pad"]["x"], w["pad"]["y"])
    assert not solid(w["start"]["x"], w["start"]["y"])
    tiles = [(s["x"], s["y"]) for s in w["structures"]]
    assert len(tiles) == len(set(tiles))


def test_content_comes_from_db(client, db):
    from app.repo import projects

    slugs = {p["slug"] for p in projects(db)}
    assert "neuromentor" in slugs and len(slugs) == 5


def test_stats_persist_view_counts(client):
    client.get("/")
    r = client.get("/stats")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_api_world(client):
    r = client.get("/api/world")
    assert r.status_code == 200
    assert r.json()["structures"]


def test_robots(client):
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert "User-agent" in r.text
