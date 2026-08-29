"""SQLAlchemy models — the portfolio's content plus page-view analytics."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    blurb: Mapped[str] = mapped_column(Text)
    highlights: Mapped[list] = mapped_column(JSON, default=list)
    stack: Mapped[list] = mapped_column(JSON, default=list)
    repo: Mapped[str] = mapped_column(String(255), default="")
    team: Mapped[bool] = mapped_column(default=False)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Experience(Base):
    __tablename__ = "experience"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(120))
    period: Mapped[str] = mapped_column(String(80))
    location: Mapped[str] = mapped_column(String(120))
    points: Mapped[list] = mapped_column(JSON, default=list)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Education(Base):
    __tablename__ = "education"

    id: Mapped[int] = mapped_column(primary_key=True)
    what: Mapped[str] = mapped_column(String(160))
    where: Mapped[str] = mapped_column(String(160))
    period: Mapped[str] = mapped_column(String(80))
    note: Mapped[str] = mapped_column(String(80), default="")
    sort: Mapped[int] = mapped_column(Integer, default=0)


class PageView(Base):
    __tablename__ = "page_views"

    path: Mapped[str] = mapped_column(String(255), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=func.now()
    )
