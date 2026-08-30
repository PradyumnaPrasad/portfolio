"""Turn the portfolio's DB content into short retrievable documents."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app import repo
from app.config import SITE


def build_documents(db: Session) -> list[dict]:
    docs: list[dict] = []

    docs.append(
        {
            "key": "about",
            "kind": "about",
            "title": SITE["name"],
            "ref": "/",
            "text": (
                f"{SITE['name']} — {SITE['tagline']} {SITE['subline']}. "
                f"Based in {SITE['location']}. Contact: {SITE['email']}."
            ),
        }
    )

    for p in repo.projects(db):
        base = f"Project '{p['name']}'. {p['blurb']} Stack: {', '.join(p['stack'])}."
        docs.append(
            {
                "key": f"project:{p['slug']}",
                "kind": "project",
                "title": p["name"],
                "ref": p["repo"],
                "text": base,
            }
        )
        for i, h in enumerate(p["highlights"]):
            docs.append(
                {
                    "key": f"project:{p['slug']}:h{i}",
                    "kind": "project",
                    "title": p["name"],
                    "ref": p["repo"],
                    "text": f"{p['name']}: {h}",
                }
            )

    for e in repo.experience(db):
        head = f"Experience: {e['role']} at {e['company']} ({e['period']}, {e['location']})."
        docs.append(
            {
                "key": f"exp:{e['company']}",
                "kind": "experience",
                "title": e["company"],
                "ref": "/",
                "text": head + " " + " ".join(e["points"]),
            }
        )
        for i, pt in enumerate(e["points"]):
            docs.append(
                {
                    "key": f"exp:{e['company']}:p{i}",
                    "kind": "experience",
                    "title": e["company"],
                    "ref": "/",
                    "text": f"At {e['company']}, {pt}",
                }
            )

    for a in repo.achievements(db):
        docs.append(
            {
                "key": f"ach:{a['label']}",
                "kind": "achievement",
                "title": a["label"],
                "ref": "/",
                "text": a["text"],
            }
        )

    for ed in repo.education(db):
        docs.append(
            {
                "key": f"edu:{ed['where']}",
                "kind": "education",
                "title": ed["where"],
                "ref": "/",
                "text": f"{ed['what']} at {ed['where']} ({ed['period']}), {ed['note']}.",
            }
        )

    return docs
