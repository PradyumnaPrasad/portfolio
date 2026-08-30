"""Shape the stored GitHub snapshot + this site's traffic for the dashboard page."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app import repo

LANG_COLOR = {
    "Python": "#3572A5",
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Jupyter Notebook": "#DA5B0B",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Java": "#B07219",
    "C++": "#F34B7D",
    "C": "#555555",
    "Shell": "#89E051",
    "Dockerfile": "#384D54",
}
_FALLBACK = ["#8b5cf6", "#22d3ee", "#f472b6", "#fbbf24", "#34d399", "#f87171"]


def _color(name: str, i: int) -> str:
    return LANG_COLOR.get(name) or _FALLBACK[i % len(_FALLBACK)]


def _heatmap(calendar: list[dict]) -> list[list[dict]]:
    """Group the daily calendar into columns of 7 (Sun..Sat), newest last."""
    if not calendar:
        return []
    by_date = {c["date"]: c["count"] for c in calendar}
    start = datetime.fromisoformat(calendar[0]["date"]).date()
    end = datetime.fromisoformat(calendar[-1]["date"]).date()
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to a Sunday
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
    """A gap-filled monthly series of 'repositories started', most recent `span`."""
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
        s["label"] = s["month"][2:]  # YY-MM
    return series


def build_dashboard(db: Session) -> dict:
    snap = repo.get_snapshot(db)
    traffic_total = repo.view_totals(db)["total"]
    top = repo.top_pages(db)

    if snap is None or not snap.payload:
        return {
            "empty": True,
            "traffic": {"total": traffic_total, "top": top},
        }

    p = snap.payload
    langs = p.get("languages", [])
    lang_total = sum(x["count"] for x in langs) or 1
    languages = [
        {
            "name": x["name"],
            "count": x["count"],
            "pct": round(x["count"] / lang_total * 100),
            "color": _color(x["name"], i),
        }
        for i, x in enumerate(langs)
    ]

    age = datetime.now(UTC) - snap.generated_at.replace(tzinfo=UTC)
    total_contrib = p.get("total_contributions", 0)
    tiles = [
        {"label": "public repos", "value": p.get("repo_count", 0)},
        {"label": "stars earned", "value": p.get("star_count", 0)},
        {"label": "languages", "value": p.get("language_count", len(langs))},
        {"label": "site views", "value": traffic_total},
    ]
    if total_contrib:
        tiles.insert(3, {"label": "contributions", "value": total_contrib})

    months = _months(p.get("repos_by_month", []))
    heatmap = _heatmap(p.get("calendar", []))

    return {
        "empty": False,
        "tiles": tiles,
        "languages": languages,
        "months": months,
        "heatmap": heatmap,
        "no_calendar": not heatmap and p.get("calendar_source") == "events",
        "calendar_source": p.get("calendar_source", "events"),
        "timeline": [
            {
                "name": t["name"],
                "year": t["created"][:4],
                "language": t["language"],
                "stars": t["stars"],
            }
            for t in p.get("timeline", [])
        ],
        "traffic": {"total": traffic_total, "top": top},
        "generated_at": snap.generated_at.isoformat(),
        "stale": age > timedelta(days=2),
    }
