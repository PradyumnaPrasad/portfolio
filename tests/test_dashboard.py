import json
from datetime import UTC, datetime
from pathlib import Path

from app.dashboard import _heatmap, _months, build_dashboard
from app.etl.leetcode import fetch_leetcode
from app.models import DashboardSnapshot

FIX = json.loads((Path(__file__).parent / "fixtures" / "snapshot.json").read_text())


def _load_snapshot(db, payload=None):
    row = db.get(DashboardSnapshot, 1) or DashboardSnapshot(id=1)
    row.payload = payload or FIX
    row.generated_at = datetime.now(UTC)
    db.add(row)
    db.commit()


def _clear(db):
    row = db.get(DashboardSnapshot, 1)
    if row:
        db.delete(row)
        db.commit()


def test_dashboard_empty_state(client, db):
    _clear(db)
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "python -m app.etl" in r.text


def test_build_dashboard_leetcode_primary(client, db):
    _load_snapshot(db)
    d = build_dashboard(db)
    assert d["empty"] is False
    labels = [t["label"] for t in d["tiles"]]
    assert labels[0] == "problems solved" and d["tiles"][0]["value"] == 406
    assert "contest rating" in labels and "public repos" in labels
    diff = {x["name"]: x["pct"] for x in d["difficulty"]}
    assert diff["Easy"] == 50  # 201 / 406
    assert d["difficulty"][2]["color"] == "#e03131"
    assert len(d["heatmap"]) >= 1
    assert d["lc_languages"][0]["name"] == "Java"
    assert d["gh_languages"][0]["name"] == "Python"


def test_dashboard_page_renders(client, db):
    _load_snapshot(db)
    r = client.get("/dashboard")
    assert r.status_code == 200
    for s in (
        "Solved by difficulty",
        "Submission calendar",
        "Solutions by language",
        "Projects on GitHub",
        "Dual_Insight_Engine",
    ):
        assert s in r.text


def test_dashboard_survives_one_source_missing(client, db):
    _load_snapshot(db, {"generated_at": FIX["generated_at"], "leetcode": FIX["leetcode"]})
    d = build_dashboard(db)
    assert d["empty"] is False
    assert "gh_languages" not in d
    assert d["tiles"][0]["value"] == 406


def test_heatmap_levels():
    weeks = _heatmap(FIX["leetcode"]["calendar"])
    flat = [x for wk in weeks for x in wk]
    assert all(0 <= x["level"] <= 4 for x in flat)
    assert max(x["level"] for x in flat) == 4


def test_months_gap_filled():
    m = _months(FIX["github"]["repos_by_month"])
    assert m[0]["month"] == "2025-03"
    assert any(x["count"] == 0 for x in m)  # gaps between active months


def test_fetch_leetcode_transform(monkeypatch):
    api = {
        "data": {
            "matchedUser": {
                "profile": {"ranking": 12345},
                "submitStatsGlobal": {
                    "acSubmissionNum": [
                        {"difficulty": "All", "count": 100},
                        {"difficulty": "Easy", "count": 60},
                        {"difficulty": "Medium", "count": 35},
                        {"difficulty": "Hard", "count": 5},
                    ]
                },
                "userCalendar": {
                    "streak": 3,
                    "totalActiveDays": 40,
                    "submissionCalendar": '{"1756512000": 4, "1756598400": 1}',
                },
                "languageProblemCount": [
                    {"languageName": "Java", "problemsSolved": 80},
                    {"languageName": "Python3", "problemsSolved": 15},
                    {"languageName": "Python", "problemsSolved": 5},
                ],
            },
            "userContestRanking": {
                "attendedContestsCount": 4,
                "rating": 1600.7,
                "globalRanking": 999,
                "topPercentage": 25.4,
            },
        }
    }

    class FakeResp:
        def json(self):
            return api

        def raise_for_status(self):
            pass

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def post(self, url, json=None):
            return FakeResp()

    monkeypatch.setattr("app.etl.leetcode.httpx.Client", lambda **kw: FakeClient())
    lc = fetch_leetcode("someone")
    assert lc["total_solved"] == 100
    assert lc["by_difficulty"] == {"Easy": 60, "Medium": 35, "Hard": 5}
    assert lc["by_language"][0] == {"name": "Java", "count": 80}
    assert {x["name"] for x in lc["by_language"]} == {"Java", "Python"}  # Python3 merged
    assert lc["contest"] == {"contests": 4, "rating": 1601, "top_percent": 25.4}
    assert len(lc["calendar"]) == 2
