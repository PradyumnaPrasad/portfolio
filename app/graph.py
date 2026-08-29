"""Builds the knowledge graph (nodes + edges) that the landing page renders.

Everything is derived from `app.content` so there is a single source of truth
for both the graph and the accessible list view.
"""

from __future__ import annotations

import re

from app import content
from app.config import SITE

# Collapse near-duplicate tech labels onto one canonical node.
_ALIASES = {
    "google gemini": "Gemini",
    "gemini 1.5 flash": "Gemini",
    "pytorch (q-learning)": "PyTorch",
    "redis + rq": "Redis",
    "tensorflow / keras": "TensorFlow",
    "tensorflow": "TensorFlow",
    "scikit-learn": "scikit-learn",
    "react": "React",
    "typescript": "TypeScript",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _canon(tech: str) -> str:
    return _ALIASES.get(tech.strip().lower(), tech.strip())


def build_graph() -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(nid: str, **kw) -> str:
        if nid not in nodes:
            nodes[nid] = {"id": nid, **kw}
        return nid

    def link(a: str, b: str, kind: str = "rel") -> None:
        edges.append({"source": a, "target": b, "kind": kind})

    me = add_node(
        "me",
        label=SITE["name"],
        type="person",
        detail={
            "kind": "person",
            "title": SITE["name"],
            "body": SITE["tagline"],
            "meta": SITE["subline"],
            "links": SITE["links"] | {"Résumé": SITE["resume_path"]},
        },
    )

    for p in content.PROJECTS:
        pid = add_node(
            f"project:{p['slug']}",
            label=p["name"],
            type="project",
            detail={
                "kind": "project",
                "title": p["name"],
                "body": p["blurb"],
                "highlights": p["highlights"],
                "stack": p["stack"],
                "repo": p["repo"],
                "team": p.get("team", False),
            },
        )
        link(me, pid, "builds")
        for tech in p["stack"]:
            label = _canon(tech)
            tid = add_node(f"tech:{_slug(label)}", label=label, type="tech")
            link(pid, tid, "uses")

    for e in content.EXPERIENCE:
        eid = add_node(
            f"exp:{_slug(e['company'])}",
            label=e["company"],
            type="experience",
            detail={
                "kind": "experience",
                "title": f"{e['role']} · {e['company']}",
                "body": f"{e['period']} — {e['location']}",
                "highlights": e["points"],
            },
        )
        link(me, eid, "worked")
        for label in ("PostgreSQL", "SQL Server", "Python", "ETL"):
            tid = add_node(f"tech:{_slug(label)}", label=label, type="tech")
            link(eid, tid, "uses")

    for i, a in enumerate(content.ACHIEVEMENTS):
        aid = add_node(
            f"ach:{i}",
            label=a["label"],
            type="achievement",
            detail={"kind": "achievement", "title": a["label"], "body": a["text"]},
        )
        link(me, aid, "won")

    return {"nodes": list(nodes.values()), "edges": edges}
