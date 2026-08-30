import json
from datetime import UTC, datetime
from pathlib import Path

from app.dashboard import _heatmap, build_dashboard
from app.etl.github import fetch_snapshot
from app.models import DashboardSnapshot

FIX = json.loads((Path(__file__).parent / "fixtures" / "gh_snapshot.json").read_text())


def _load_snapshot(db):
    row = db.get(DashboardSnapshot, 1) or DashboardSnapshot(id=1)
    row.payload = FIX
    row.generated_at = datetime.now(UTC)
    db.add(row)
    db.commit()


def test_dashboard_empty_state(client, db):
    row = db.get(DashboardSnapshot, 1)
    if row:
        db.delete(row)
        db.commit()
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "python -m app.etl" in r.text


def test_build_dashboard_from_snapshot(client, db):
    _load_snapshot(db)
    d = build_dashboard(db)
    assert d["empty"] is False
    assert d["tiles"][0]["value"] == 17
    langs = {x["name"]: x["pct"] for x in d["languages"]}
    assert langs["Python"] == 59  # 10 / 17
    assert d["languages"][0]["color"] == "#3572A5"
    assert len(d["heatmap"]) >= 1
    assert d["stale"] is False


def test_dashboard_page_renders_charts(client, db):
    _load_snapshot(db)
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "Languages" in r.text and "Commit calendar" in r.text
    assert "Dual_Insight_Engine" in r.text


def test_heatmap_levels():
    weeks = _heatmap(FIX["calendar"])
    flat = [d for wk in weeks for d in wk]
    assert all(0 <= d["level"] <= 4 for d in flat)
    assert max(d["level"] for d in flat) == 4  # the busiest day maxes out


def test_fetch_snapshot_shape(monkeypatch):
    """fetch_snapshot transforms API JSON without hitting the network."""

    class FakeResp:
        status_code = 200
        links: dict = {}

        def __init__(self, data):
            self._data = data

        def json(self):
            return self._data

        def raise_for_status(self):
            pass

    repos = [
        {
            "name": "a",
            "language": "Python",
            "fork": False,
            "stargazers_count": 2,
            "created_at": "2025-01-01T00:00:00Z",
            "pushed_at": "2025-06-01T00:00:00Z",
        },
        {
            "name": "b",
            "language": "Go",
            "fork": True,
            "stargazers_count": 9,
            "created_at": "2025-02-01T00:00:00Z",
            "pushed_at": "2025-02-01T00:00:00Z",
        },
    ]
    events = [
        {
            "type": "PushEvent",
            "created_at": "2026-08-29T10:00:00Z",
            "payload": {"commits": [1, 2, 3]},
        },
        {"type": "WatchEvent", "created_at": "2026-08-29T11:00:00Z", "payload": {}},
    ]

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def get(self, url, params=None):
            return FakeResp(repos if "/repos" in url else events)

    monkeypatch.setattr("app.etl.github._client", lambda token: FakeClient())
    snap = fetch_snapshot("someone")
    assert snap["repo_count"] == 1  # fork excluded
    assert snap["star_count"] == 2
    assert snap["languages"] == [{"name": "Python", "count": 1}]
    assert snap["total_contributions"] == 3
    assert snap["calendar_source"] == "events"
