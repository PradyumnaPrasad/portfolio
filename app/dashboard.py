"""Shape the stored activity snapshot (LeetCode + GitHub) + this site's traffic
for the /dashboard page."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app import repo

LANG_COLOR = {
    "Python": "#3572A5",
    "Java": "#B07219",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Jupyter Notebook": "#DA5B0B",
    "SQL": "#e38c00",
    "C++": "#F34B7D",
    "C": "#8a8a8a",
    "HTML": "#E34C26",
    "Shell": "#89E051",
}
_FALLBACK = ["#8b5cf6", "#22d3ee", "#f472b6", "#fbbf24", "#34d399", "#f87171"]
DIFF_COLOR = {"Easy": "#37b24d", "Medium": "#f59f00", "Hard": "#e03131"}


def _color(name: str, i: int) -> str:
    return LANG_COLOR.get(name) or _FALLBACK[i % len(_FALLBACK)]


def _bars(items: list[dict]) -> list[dict]:
    total = sum(x["count"] for x in items) or 1
    return [
        {
            "name": x["name"],
            "count": x["count"],
            "pct": round(x["count"] / total * 100),
            "color": _color(x["name"], i),
        }
        for i, x in enumerate(items)
    ]


def _heatmap(calendar: list[dict]) -> list[list[dict]]:
    """Group the daily calendar into columns of 7 (Sun..Sat), oldest first."""
    if not calendar:
        return []
    by_date = {c["date"]: c["count"] for c in calendar}
    start = datetime.fromisoformat(calendar[0]["date"]).date()
    end = datetime.fromisoformat(calendar[-1]["date"]).date()
    start -= timedelta(days=(start.weekday() + 1) % 7)
    peak = max((c["count"] for c in calendar), default=0) or 1

    weeks, day = [], start
    while day <= end:
        col = []
        for _ in range(7):
            n = by_date.get(day.isoformat(), 0)
            level = 0 if n == 0 else min(4, 1 + math.floor(n / peak * 3))
            col.append({"date": day.isoformat(), "count": n, "level": level})
            day += timedelta(days=1)
        weeks.append(col)
    return weeks


def _months(repos_by_month: list[dict], span: int = 24) -> list[dict]:
    if not repos_by_month:
        return []
    counts = {r["month"]: r["count"] for r in repos_by_month}
    first = datetime.fromisoformat(repos_by_month[0]["month"] + "-01")
    now = datetime.now(UTC).replace(tzinfo=None)
    series, cur = [], first
    while cur <= now:
        key = cur.strftime("%Y-%m")
        series.append({"month": key, "count": counts.get(key, 0)})
        cur = (cur.replace(day=28) + timedelta(days=8)).replace(day=1)
    series = series[-span:]
    peak = max((s["count"] for s in series), default=0) or 1
    for s in series:
        s["pct"] = round(s["count"] / peak * 100)
        s["label"] = s["month"][2:]
    return series


def build_dashboard(db: Session) -> dict:
    snap = repo.get_snapshot(db)
    traffic_total = repo.view_totals(db)["total"]
    top = repo.top_pages(db)
    traffic = {"total": traffic_total, "top": top}

    p = snap.payload if snap and snap.payload else {}
    lc = p.get("leetcode")
    gh = p.get("github")

    if not lc and not gh:
        return {"empty": True, "traffic": traffic}

    out: dict = {"empty": False, "traffic": traffic}
    age = datetime.now(UTC) - snap.generated_at.replace(tzinfo=UTC)
    out["stale"] = age > timedelta(days=3)
    out["generated_at"] = snap.generated_at.isoformat()

    tiles: list[dict] = []
    if lc:
        d = lc["by_difficulty"]
        tiles += [
            {"label": "problems solved", "value": lc["total_solved"]},
            {"label": "day streak", "value": lc["streak"]},
            {"label": "active days", "value": lc["active_days"]},
        ]
        if lc.get("contest"):
            tiles.append({"label": "contest rating", "value": lc["contest"]["rating"]})
        out["difficulty"] = [
            {
                "name": k,
                "count": d[k],
                "pct": round(d[k] / (lc["total_solved"] or 1) * 100),
                "color": DIFF_COLOR[k],
            }
            for k in ("Easy", "Medium", "Hard")
        ]
        out["heatmap"] = _heatmap(lc.get("calendar", []))
        out["lc_languages"] = _bars(lc.get("by_language", []))
        out["contest"] = lc.get("contest")
        out["lc_username"] = lc["username"]

    if gh:
        tiles.append({"label": "public repos", "value": gh["repo_count"]})
        out["gh_languages"] = _bars(gh.get("languages", []))
        out["months"] = _months(gh.get("repos_by_month", []))
        out["timeline"] = [
            {
                "name": t["name"],
                "year": t["created"][:4],
                "language": t["language"],
                "stars": t["stars"],
            }
            for t in gh.get("timeline", [])
        ]

    tiles.append({"label": "site views", "value": traffic_total})
    out["tiles"] = tiles
    return out
