"""The portfolio as a small top-down RPG world.

Each structure is a building you can walk into; its `detail` is the quest log
shown when you enter. Terrain is a tile string, all derived so `app.content`
stays the single source of truth.
"""

from __future__ import annotations

from app import content
from app.config import SITE

# T = tree, ~ = water, . = grass. Border only; the interior is open.
TERRAIN = [
    "TT~~~~~~~~~~~~~~~~TT",
    "T..................T",
    "T..................T",
    "T..................T",
    "~..................~",
    "~..................~",
    "~..................~",
    "T..................T",
    "T..................T",
    "T..................T",
    "T..................T",
    "TT~~~~~~~~~~~~~~~~TT",
]

# decorative trees (also solid) placed clear of buildings and their door mats
DECOR_TREES = [(7, 2), (12, 2), (7, 7), (12, 7), (2, 10), (17, 10)]


def _proj(slug: str, roof: str, short: str) -> dict:
    p = {x["slug"]: x for x in content.PROJECTS}[slug]
    return {
        "roof": roof,
        "name": short,
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


def build_world() -> dict:
    e = content.EXPERIENCE[0]
    ach = {a["label"]: a["text"] for a in content.ACHIEVEMENTS}

    # x, y is the building tile; the door mat is (x, y + 1)
    structures = [
        {
            "x": 3,
            "y": 2,
            "roof": "#c9a24a",
            "name": "Home",
            "detail": {
                "kind": "home base",
                "title": SITE["name"],
                "body": SITE["tagline"],
                "objectives": [
                    f"{x['what']} · {x['where']} ({x['period']}) — {x['note']}"
                    for x in content.EDUCATION
                ],
                "meta": SITE["location"],
                "links": SITE["links"] | {"Résumé": SITE["resume_path"]},
            },
        },
        {
            "x": 15,
            "y": 2,
            "roof": "#4a86c9",
            "name": "Hexango HQ",
            "detail": {
                "kind": "guild — internship",
                "title": f"{e['role']} · {e['company']}",
                "body": f"{e['period']} — {e['location']}",
                "objectives": e["points"],
                "loot": ["PostgreSQL", "SQL Server", "PL/pgSQL", "ETL", "Python"],
            },
        },
        {"x": 3, "y": 5, **_proj("neuromentor", "#c14a3a", "NeuroMentor")},
        {"x": 9, "y": 5, **_proj("dual-insight-engine", "#8a4ac1", "Dual Insight")},
        {"x": 15, "y": 5, **_proj("ai-resume-maker", "#3aa38a", "AI Resume Maker")},
        {"x": 3, "y": 8, **_proj("distributed-web-scraper", "#7a7a3a", "Web Scraper")},
        {"x": 8, "y": 8, **_proj("isl-gesture-detection", "#c17a3a", "Gesture ISL")},
        {
            "x": 15,
            "y": 8,
            "roof": "#d4b23a",
            "name": "Trophy Hall",
            "detail": {
                "kind": "achievements",
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
            "x": 12,
            "y": 8,
            "roof": "#5a9c5a",
            "name": "Workshop",
            "detail": {
                "kind": "what's next",
                "title": "The Workshop",
                "body": "Being built onto this very site:",
                "objectives": [
                    "A live data dashboard — GitHub activity ETL, refreshed nightly.",
                    "Semantic project search over pgvector.",
                    "A RAG 'ask my portfolio' chatbot on Gemini.",
                ],
                "meta": SITE["email"],
                "links": SITE["links"],
            },
        },
    ]

    # a stat pad (walk onto it) rather than a building
    pad = {
        "x": 6,
        "y": 10,
        "detail": {
            "kind": "skill tree",
            "title": "Skill tree",
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
        "cols": len(TERRAIN[0]),
        "rows": len(TERRAIN),
        "terrain": TERRAIN,
        "trees": DECOR_TREES,
        "structures": structures,
        "pad": pad,
        "start": {"x": 9, "y": 10},
        "title": SITE["name"],
        "tagline": SITE["tagline"],
    }
