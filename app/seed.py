"""Seed the database from ``app.content`` (the human-editable source of truth).

Idempotent and authoritative: on every startup the content tables are rebuilt
from ``content.py``, so edits there always propagate. These tables are tiny and
nothing holds a foreign key into them.
"""

from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app import content
from app.models import Achievement, Education, Experience, Project


def seed(db: Session) -> None:
    db.execute(delete(Project))
    db.execute(delete(Experience))
    db.execute(delete(Achievement))
    db.execute(delete(Education))

    for i, p in enumerate(content.PROJECTS):
        db.add(
            Project(
                slug=p["slug"],
                name=p["name"],
                blurb=p["blurb"],
                highlights=p["highlights"],
                stack=p["stack"],
                repo=p["repo"],
                team=p.get("team", False),
                sort=i,
            )
        )
    for i, e in enumerate(content.EXPERIENCE):
        db.add(
            Experience(
                company=e["company"],
                role=e["role"],
                period=e["period"],
                location=e["location"],
                points=e["points"],
                sort=i,
            )
        )
    for i, a in enumerate(content.ACHIEVEMENTS):
        db.add(Achievement(label=a["label"], text=a["text"], sort=i))
    for i, ed in enumerate(content.EDUCATION):
        db.add(
            Education(
                what=ed["what"],
                where=ed["where"],
                period=ed["period"],
                note=ed["note"],
                sort=i,
            )
        )
    db.commit()
