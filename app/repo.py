"""Read helpers: pull content out of the database in the shape the views expect.

These return plain dicts/lists (not ORM objects) so templates and the world
builder stay decoupled from the persistence layer.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Achievement, Education, Experience, PageView, Project


def projects(db: Session) -> list[dict]:
    rows = db.scalars(select(Project).order_by(Project.sort, Project.id)).all()
    return [
        {
            "slug": p.slug,
            "name": p.name,
            "blurb": p.blurb,
            "highlights": p.highlights,
            "stack": p.stack,
            "repo": p.repo,
            "team": p.team,
        }
        for p in rows
    ]


def experience(db: Session) -> list[dict]:
    rows = db.scalars(select(Experience).order_by(Experience.sort, Experience.id)).all()
    return [
        {
            "company": e.company,
            "role": e.role,
            "period": e.period,
            "location": e.location,
            "points": e.points,
        }
        for e in rows
    ]


def achievements(db: Session) -> list[dict]:
    rows = db.scalars(select(Achievement).order_by(Achievement.sort, Achievement.id)).all()
    return [{"label": a.label, "text": a.text} for a in rows]


def education(db: Session) -> list[dict]:
    rows = db.scalars(select(Education).order_by(Education.sort, Education.id)).all()
    return [{"what": e.what, "where": e.where, "period": e.period, "note": e.note} for e in rows]


def flush_views(db: Session, counts: dict[str, int]) -> None:
    """Add the in-memory view deltas to the persistent counters."""
    for path, delta in counts.items():
        row = db.get(PageView, path)
        if row is None:
            db.add(PageView(path=path, count=delta))
        else:
            row.count += delta
    db.commit()


def view_totals(db: Session) -> dict:
    rows = db.scalars(select(PageView)).all()
    views = {r.path: r.count for r in rows}
    return {"views": views, "total": sum(views.values())}
