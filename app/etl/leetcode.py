"""Extract + transform LeetCode activity via the public GraphQL endpoint.

No auth. Gives a full-year submission calendar, solve counts by difficulty and
language, streak, and contest rating.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime

import httpx

GRAPHQL = "https://leetcode.com/graphql"

_QUERY = """
query dashboard($u: String!) {
  matchedUser(username: $u) {
    profile { ranking }
    submitStatsGlobal { acSubmissionNum { difficulty count } }
    userCalendar { streak totalActiveDays submissionCalendar }
    languageProblemCount { languageName problemsSolved }
  }
  userContestRanking(username: $u) {
    attendedContestsCount rating globalRanking topPercentage
  }
}
"""

_LANG_ALIAS = {
    "Python3": "Python",
    "C++": "C++",
    "MySQL": "SQL",
    "MS SQL Server": "SQL",
    "Oracle": "SQL",
}


def fetch_leetcode(username: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://leetcode.com/u/{username}/",
    }
    with httpx.Client(headers=headers, timeout=20) as c:
        r = c.post(GRAPHQL, json={"query": _QUERY, "variables": {"u": username}})
        r.raise_for_status()
        data = r.json()["data"]

    mu = data.get("matchedUser")
    if not mu:
        raise ValueError(f"LeetCode user '{username}' not found")

    ac = {x["difficulty"]: x["count"] for x in mu["submitStatsGlobal"]["acSubmissionNum"]}
    cal_raw = json.loads(mu["userCalendar"].get("submissionCalendar") or "{}")
    calendar = sorted(
        (
            {"date": datetime.fromtimestamp(int(ts), UTC).date().isoformat(), "count": n}
            for ts, n in cal_raw.items()
        ),
        key=lambda d: d["date"],
    )

    langs: Counter[str] = Counter()
    for x in mu.get("languageProblemCount", []):
        langs[_LANG_ALIAS.get(x["languageName"], x["languageName"])] += x["problemsSolved"]

    cr = data.get("userContestRanking")
    contest = (
        {
            "contests": cr["attendedContestsCount"],
            "rating": round(cr["rating"]),
            "top_percent": round(cr["topPercentage"], 1),
        }
        if cr and cr.get("attendedContestsCount")
        else None
    )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "username": username,
        "total_solved": ac.get("All", 0),
        "by_difficulty": {
            "Easy": ac.get("Easy", 0),
            "Medium": ac.get("Medium", 0),
            "Hard": ac.get("Hard", 0),
        },
        "streak": mu["userCalendar"].get("streak", 0),
        "active_days": mu["userCalendar"].get("totalActiveDays", 0),
        "ranking": mu["profile"].get("ranking"),
        "calendar": calendar,
        "by_language": [{"name": k, "count": v} for k, v in langs.most_common()],
        "contest": contest,
    }
