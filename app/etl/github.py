"""Extract + transform GitHub activity into a dashboard snapshot.

Uses the public REST API (no token needed — a couple of requests per run).
If ``GITHUB_TOKEN`` is set, the yearly contribution calendar is pulled from
the GraphQL API instead of being approximated from the recent events feed.
"""

from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import UTC, datetime

import httpx

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"
UA = {"User-Agent": "pradyumna-portfolio-etl", "Accept": "application/vnd.github+json"}


def _client(token: str | None) -> httpx.Client:
    headers = dict(UA)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(headers=headers, timeout=20)


def _all_repos(c: httpx.Client, username: str) -> list[dict]:
    repos: list[dict] = []
    url = f"{API}/users/{username}/repos"
    params = {"per_page": 100, "sort": "pushed"}
    while url:
        r = c.get(url, params=params)
        r.raise_for_status()
        repos.extend(r.json())
        url = r.links.get("next", {}).get("url")
        params = None
    return repos


def _calendar_from_events(c: httpx.Client, username: str) -> tuple[list[dict], int]:
    by_day: dict[str, int] = defaultdict(int)
    url = f"{API}/users/{username}/events/public"
    params = {"per_page": 100}
    for _ in range(3):  # up to 300 events
        r = c.get(url, params=params)
        if r.status_code != 200:
            break
        for ev in r.json():
            if ev.get("type") == "PushEvent":
                day = ev["created_at"][:10]
                by_day[day] += len(ev.get("payload", {}).get("commits", []))
        url = r.links.get("next", {}).get("url")
        params = None
        if not url:
            break
    cal = [{"date": d, "count": n} for d, n in sorted(by_day.items())]
    return cal, sum(by_day.values())


def _calendar_from_graphql(c: httpx.Client, username: str) -> tuple[list[dict], int]:
    q = """
    query($login:String!){
      user(login:$login){
        contributionsCollection{
          contributionCalendar{
            totalContributions
            weeks{ contributionDays{ date contributionCount } }
          }
        }
      }
    }"""
    r = c.post(GRAPHQL, json={"query": q, "variables": {"login": username}})
    r.raise_for_status()
    cc = r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    cal = [
        {"date": d["date"], "count": d["contributionCount"]}
        for w in cc["weeks"]
        for d in w["contributionDays"]
    ]
    return cal, cc["totalContributions"]


def fetch_snapshot(username: str, token: str | None = None) -> dict:
    token = token or os.getenv("GITHUB_TOKEN") or None
    with _client(token) as c:
        repos = _all_repos(c, username)
        owned = [r for r in repos if not r["fork"]]

        langs = Counter(r["language"] for r in owned if r["language"])
        started = Counter(r["created_at"][:7] for r in owned)  # YYYY-MM
        repos_by_month = [{"month": m, "count": n} for m, n in sorted(started.items())]
        timeline = sorted(
            (
                {
                    "name": r["name"],
                    "created": r["created_at"][:10],
                    "pushed": r["pushed_at"][:10],
                    "language": r["language"],
                    "stars": r["stargazers_count"],
                }
                for r in owned
            ),
            key=lambda x: x["created"],
        )

        if token:
            try:
                calendar, total = _calendar_from_graphql(c, username)
                source = "graphql"
            except Exception:
                calendar, total = _calendar_from_events(c, username)
                source = "events"
        else:
            calendar, total = _calendar_from_events(c, username)
            source = "events"

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "username": username,
        "repo_count": len(owned),
        "star_count": sum(r["stargazers_count"] for r in owned),
        "language_count": len(langs),
        "languages": [{"name": k, "count": v} for k, v in langs.most_common()],
        "repos_by_month": repos_by_month,
        "timeline": timeline,
        "calendar": calendar,
        "total_contributions": total,
        "calendar_source": source,
    }
