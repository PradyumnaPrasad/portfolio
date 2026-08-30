"""The portfolio as a small top-down RPG village.

Each structure is a building you walk into; its `detail` is the quest log
shown on entry. Content comes from the database (see `app.repo`); terrain and
paths are generated.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app import repo
from app.config import SITE

COLS, ROWS = 21, 16


def _terrain() -> list[str]:
    rows = []
    for y in range(ROWS):
        line = []
        for x in range(COLS):
            edge_x = x == 0 or x == COLS - 1
            edge_y = y == 0 or y == ROWS - 1
            if edge_y:
                line.append("T" if x < 2 or x >= COLS - 2 else "~")
            elif edge_x:
                line.append("~" if 5 <= y <= 10 else "T")
            else:
                line.append(".")
        rows.append("".join(line))
    return rows


def _paths() -> list[list[int]]:
    tiles: set[tuple[int, int]] = set()
    for x in (4, 10, 16):
        for y in range(3, 15):
            tiles.add((x, y))
    for x in (7, 13):
        for y in range(11, 15):
            tiles.add((x, y))
    for y in (3, 7, 11, 14):
        for x in range(4, 17):
            tiles.add((x, y))
    return sorted([x, y] for x, y in tiles)


def _proj(by_slug: dict, slug: str, roof: str, short: str) -> dict:
    p = by_slug[slug]
    return {
        "roof": roof,
        "name": short,
        "icon": "house",
        "detail": {
            "kind": "project",
            "title": p["name"],
            "body": p["blurb"],
            "objectives": p["highlights"],
            "loot": p["stack"],
            "link": p["repo"],
            "link_label": "source →",
            "team": p.get("team", False),
        },
    }


def build_world(db: Session) -> dict:
    by_slug = {p["slug"]: p for p in repo.projects(db)}
    exp = repo.experience(db)
    e = exp[0] if exp else {"role": "", "company": "", "period": "", "location": "", "points": []}
    ach = {a["label"]: a["text"] for a in repo.achievements(db)}
    edu = repo.education(db)

    snap = repo.get_snapshot(db)
    payload = snap.payload if snap and snap.payload else {}
    lc, gh = payload.get("leetcode"), payload.get("github")
    if lc or gh:
        obs_lines = ["A live dashboard, refreshed nightly by an ETL job:"]
        if lc:
            c = lc.get("contest")
            top = f", top {c['top_percent']}%" if c else ""
            obs_lines.append(
                f"{lc['total_solved']} LeetCode problems solved · {lc['streak']}-day streak{top}."
            )
        if gh:
            obs_lines.append(f"{gh['repo_count']} public repos on GitHub.")
        obs_lines.append("Walk in for the charts.")
    else:
        obs_lines = [
            "A live dashboard of my coding activity — a LeetCode submission",
            "calendar, solve counts, GitHub projects, and this site's traffic.",
            "Built by a nightly ETL job. Walk in to see it.",
        ]

    def P(slug, roof, short):
        return _proj(by_slug, slug, roof, short)

    structures = [
        {
            "x": 4,
            "y": 2,
            "roof": "#c9a24a",
            "name": "Home",
            "icon": "home",
            "detail": {
                "kind": "home base",
                "title": SITE["name"],
                "body": SITE["tagline"],
                "objectives": [
                    f"{x['what']} · {x['where']} ({x['period']}) — {x['note']}" for x in edu
                ],
                "meta": SITE["location"],
            },
        },
        {
            "x": 10,
            "y": 2,
            "roof": "#4a86c9",
            "name": "Hexango HQ",
            "icon": "guild",
            "detail": {
                "kind": "guild · internship",
                "title": f"{e['role']} · {e['company']}",
                "body": f"{e['period']} — {e['location']}",
                "objectives": e["points"],
                "loot": ["PostgreSQL", "SQL Server", "PL/pgSQL", "ETL", "Python"],
            },
        },
        {
            "x": 16,
            "y": 2,
            "roof": "#8a4ac1",
            "name": "Post Office",
            "icon": "mail",
            "detail": {
                "kind": "get in touch",
                "title": "Post Office",
                "body": "Send a raven. Fastest reply by email.",
                "meta": SITE["email"],
                "links": SITE["links"] | {"Résumé": SITE["resume_path"]},
            },
        },
        {"x": 4, "y": 6, **P("neuromentor", "#c14a3a", "NeuroMentor")},
        {"x": 10, "y": 6, **P("dual-insight-engine", "#3aa38a", "Dual Insight")},
        {"x": 16, "y": 6, **P("ai-resume-maker", "#d08a2c", "AI Resume Maker")},
        {"x": 4, "y": 10, **P("distributed-web-scraper", "#7a7a3a", "Web Scraper")},
        {"x": 10, "y": 10, **P("isl-gesture-detection", "#c17ad0", "Gesture ISL")},
        {
            "x": 16,
            "y": 10,
            "roof": "#d4b23a",
            "name": "Trophy Hall",
            "icon": "trophy",
            "detail": {
                "kind": "hall of fame",
                "title": "Trophy Hall",
                "objectives": [
                    ach["MIT Hackathon '25"],
                    ach["SIT Pitchathon"],
                    ach["400+ DSA"],
                    ach["AI Brewery Lead"],
                ],
            },
        },
        {
            "x": 7,
            "y": 13,
            "roof": "#5a9c5a",
            "name": "Workshop",
            "icon": "hammer",
            "detail": {
                "kind": "live tools",
                "title": "The Workshop",
                "body": "Three things running on this site:",
                "objectives": [
                    "Semantic search over everything in my portfolio.",
                    "A RAG 'ask my portfolio' chatbot (Gemini).",
                    "A small scikit-learn classifier you can poke at.",
                ],
                "link": "/workshop",
                "link_label": "enter the workshop →",
            },
        },
        {
            "x": 13,
            "y": 13,
            "roof": "#3f7fae",
            "name": "Observatory",
            "icon": "telescope",
            "detail": {
                "kind": "live data",
                "title": "The Observatory",
                "body": " ".join(obs_lines[:2]),
                "objectives": obs_lines[2:],
                "link": "/dashboard",
                "link_label": "open the dashboard →",
            },
        },
    ]

    pad = {
        "x": 16,
        "y": 13,
        "detail": {
            "kind": "skill tree",
            "title": "Skill Tree",
            "stats": [
                ["Backend", 9],
                ["Data / SQL", 8],
                ["AI / ML", 8],
                ["DSA", 8],
                ["DevOps", 6],
                ["Frontend", 6],
            ],
            "loot": [
                "Python",
                "Java",
                "C++",
                "SQL",
                "FastAPI",
                "Docker",
                "Redis",
                "LangChain",
                "TensorFlow",
                "scikit-learn",
                "PostgreSQL",
                "ChromaDB",
            ],
        },
    }

    return {
        "cols": COLS,
        "rows": ROWS,
        "terrain": _terrain(),
        "paths": _paths(),
        "trees": [
            [2, 4],
            [18, 4],
            [2, 9],
            [18, 9],
            [2, 12],
            [18, 12],
            [6, 4],
            [14, 4],
            [6, 12],
            [14, 12],
            [9, 12],
            [15, 12],
        ],
        "structures": structures,
        "pad": pad,
        "start": {"x": 10, "y": 14},
        "title": SITE["name"],
        "tagline": SITE["tagline"],
    }
