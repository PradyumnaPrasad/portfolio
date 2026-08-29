"""Seed the database from ``app.content`` (the human-editable source of truth).

Idempotent: safe to run on every startup. Content edits in ``content.py`` are
re-applied; rows no longer present are left untouched (delete by hand if needed).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import content
from app.models import Achievement, Education, Experience, Project


def seed(db: Session) -> None:
    for i, p in enumerate(content.PROJECTS):
        row = db.scalar(select(Project).where(Project.slug == p["slug"]))
        row = row or Project(slug=p["slug"])
        row.name = p["name"]
        row.blurb = p["blurb"]
        row.highlights = p["highlights"]
        row.stack = p["stack"]
        row.repo = p["repo"]
        row.team = p.get("team", False)
        row.sort = i
        db.add(row)

    if not db.scalar(select(Experience).limit(1)):
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

    if not db.scalar(select(Achievement).limit(1)):
        for i, a in enumerate(content.ACHIEVEMENTS):
            db.add(Achievement(label=a["label"], text=a["text"], sort=i))

    if not db.scalar(select(Education).limit(1)):
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
