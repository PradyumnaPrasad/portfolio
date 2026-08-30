"""Thin client for the Google Gemini REST API (free tier).

No SDK — just httpx. Everything degrades gracefully when GEMINI_API_KEY is
unset: ``embed`` returns None, ``generate`` raises ``GeminiUnavailable``.
"""

from __future__ import annotations

import os

import httpx

BASE = "https://generativelanguage.googleapis.com/v1beta"
EMBED_MODEL = "models/gemini-embedding-001"
CHAT_MODEL = "models/gemini-3.6-flash"
EMBED_DIM = 768


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
    out: list[list[float]] = []
    with httpx.Client(timeout=30) as c:
        for t in texts:
            r = c.post(
                f"{BASE}/{EMBED_MODEL}:embedContent",
                params={"key": key},
                json={
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": EMBED_DIM,
                },
            )
            r.raise_for_status()
            out.append(r.json()["embedding"]["values"])
    return out


def generate(system: str, user: str, *, max_tokens: int = 1400) -> str:
    key = api_key()
    if not key:
        raise GeminiUnavailable("GEMINI_API_KEY is not set")
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens},
    }
    with httpx.Client(timeout=60) as c:
        r = c.post(f"{BASE}/{CHAT_MODEL}:generateContent", params={"key": key}, json=body)
        if r.status_code == 429:
            raise GeminiUnavailable("rate limited by Gemini — try again shortly")
        r.raise_for_status()
        data = r.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError) as exc:  # blocked, or thinking used the whole budget
        raise GeminiUnavailable("Gemini returned no answer") from exc
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise GeminiUnavailable("Gemini returned no answer")
    return text
