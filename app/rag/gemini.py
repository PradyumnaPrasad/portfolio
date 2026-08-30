"""Thin client for the Google Gemini REST API (free tier).

No SDK — just httpx. Everything degrades gracefully when GEMINI_API_KEY is
unset: ``embed`` returns None, ``generate`` raises ``GeminiUnavailable``.
"""

from __future__ import annotations

import os

import httpx

BASE = "https://generativelanguage.googleapis.com/v1beta"
EMBED_MODEL = "models/text-embedding-004"
CHAT_MODEL = "models/gemini-2.0-flash"


class GeminiUnavailable(RuntimeError):
    pass


def api_key() -> str | None:
    return os.getenv("GEMINI_API_KEY", "").strip() or None


def enabled() -> bool:
    return api_key() is not None


def embed(texts: list[str]) -> list[list[float]] | None:
    key = api_key()
    if not key or not texts:
        return None
    reqs = [{"model": EMBED_MODEL, "content": {"parts": [{"text": t}]}} for t in texts]
    with httpx.Client(timeout=30) as c:
        r = c.post(
            f"{BASE}/{EMBED_MODEL}:batchEmbedContents",
            params={"key": key},
            json={"requests": reqs},
        )
        r.raise_for_status()
        return [e["values"] for e in r.json()["embeddings"]]


def generate(system: str, user: str, *, max_tokens: int = 500) -> str:
    key = api_key()
    if not key:
        raise GeminiUnavailable("GEMINI_API_KEY is not set")
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens},
    }
    with httpx.Client(timeout=45) as c:
        r = c.post(f"{BASE}/{CHAT_MODEL}:generateContent", params={"key": key}, json=body)
        if r.status_code == 429:
            raise GeminiUnavailable("rate limited by Gemini — try again shortly")
        r.raise_for_status()
        data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as exc:  # blocked / empty
        raise GeminiUnavailable("Gemini returned no answer") from exc
