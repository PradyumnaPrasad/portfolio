from fastapi.testclient import TestClient

from app.graph import build_graph
from app.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_home_renders_graph_and_fallback():
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert 'id="graph"' in body
    assert 'id="graph-data"' in body
    # accessible fallback content is still in the DOM for SEO / no-JS
    assert "Dual Insight Engine" in body
    assert "Hexango" in body


def test_api_graph_shape():
    r = client.get("/api/graph")
    assert r.status_code == 200
    g = r.json()
    ids = {n["id"] for n in g["nodes"]}
    assert "me" in ids
    assert any(i.startswith("project:") for i in ids)
    for e in g["edges"]:
        assert e["source"] in ids and e["target"] in ids


def test_graph_connectivity():
    g = build_graph()
    linked = set()
    for e in g["edges"]:
        linked.add(e["source"])
        linked.add(e["target"])
    # every node participates in at least one edge
    assert linked == {n["id"] for n in g["nodes"]}


def test_robots():
    r = client.get("/robots.txt")
    assert r.status_code == 200
    assert "User-agent" in r.text
