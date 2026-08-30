"""Chunk storage + retrieval.

Embeddings (Gemini) are stored as JSON. At ~40 short documents an in-Python
cosine scan is instant, so there is no vector index yet — the schema is ready
for pgvector if the corpus ever grows.
"""

from __future__ import annotations

import hashlib
import math
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk
from app.rag import gemini
from app.rag.corpus import build_documents

_WORD = re.compile(r"[a-z0-9]+")


def _hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:16]


def reindex(db: Session) -> dict:
    docs = build_documents(db)
    by_key = {d["key"] for d in docs}

    existing = {c.key: c for c in db.scalars(select(Chunk)).all()}
    for key in list(existing):
        if key not in by_key:
            db.delete(existing.pop(key))

    stale: list[Chunk] = []
    for d in docs:
        c = existing.get(d["key"]) or Chunk(key=d["key"])
        h = _hash(d["text"])
        if (
            c.key not in existing
            or c.content_hash != h
            or (gemini.enabled() and c.embedding is None)
        ):
            c.kind, c.title, c.ref, c.text, c.content_hash = (
                d["kind"],
                d["title"],
                d["ref"],
                d["text"],
                h,
            )
            c.embedding = None
            stale.append(c)
        db.add(c)

    embedded = 0
    if stale and gemini.enabled():
        vectors = gemini.embed([c.text for c in stale])
        if vectors:
            for c, v in zip(stale, vectors, strict=True):
                c.embedding = v
            embedded = len(stale)

    db.commit()
    return {"documents": len(docs), "reembedded": embedded, "embeddings": gemini.enabled()}


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _keyword_score(query_words: set[str], text: str) -> float:
    words = set(_WORD.findall(text.lower()))
    if not words:
        return 0.0
    return len(query_words & words) / math.sqrt(len(query_words) * len(words))


def search(db: Session, query: str, k: int = 5) -> list[dict]:
    query = query.strip()
    if not query:
        return []
    chunks = db.scalars(select(Chunk)).all()
    if not chunks:
        return []

    scored: list[tuple[float, Chunk]] = []
    qvec = gemini.embed([query]) if gemini.enabled() else None
    if qvec and any(c.embedding for c in chunks):
        q = qvec[0]
        for c in chunks:
            if c.embedding:
                scored.append((_cosine(q, c.embedding), c))
        mode = "semantic"
    else:
        qw = set(_WORD.findall(query.lower()))
        scored = [(_keyword_score(qw, c.text), c) for c in chunks]
        mode = "keyword"

    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for score, c in scored[:k]:
        if score <= 0:
            continue
        out.append(
            {
                "title": c.title,
                "kind": c.kind,
                "text": c.text,
                "ref": c.ref,
                "score": round(float(score), 3),
                "mode": mode,
            }
        )
    return out
