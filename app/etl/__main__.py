"""Run the activity ETL and store the combined snapshot.

    python -m app.etl                       # uses env / defaults
    python -m app.etl --gh USER --lc USER

Fetches GitHub and LeetCode independently; whichever succeeds is stored.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

from app.db import SessionLocal, engine
from app.etl.github import fetch_snapshot
from app.etl.leetcode import fetch_leetcode
from app.models import Base, DashboardSnapshot


def _arg(argv: list[str], flag: str, default: str) -> str:
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    gh_user = _arg(argv, "--gh", os.getenv("GITHUB_USERNAME", "PradyumnaPrasad"))
    lc_user = _arg(argv, "--lc", os.getenv("LEETCODE_USERNAME", "Pradyumna_Prasad"))

    payload: dict = {"generated_at": datetime.now(UTC).isoformat()}

    try:
        print(f"[etl] GitHub: {gh_user} ...")
        payload["github"] = fetch_snapshot(gh_user)
        g = payload["github"]
        print(f"[etl]   {g['repo_count']} repos · {g['star_count']} stars")
    except Exception as exc:  # noqa: BLE001
        print(f"[etl]   GitHub failed: {exc}")

    try:
        print(f"[etl] LeetCode: {lc_user} ...")
        payload["leetcode"] = fetch_leetcode(lc_user)
        lc = payload["leetcode"]
        print(
            f"[etl]   {lc['total_solved']} solved · {lc['streak']}-day streak · "
            f"{lc['active_days']} active days"
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[etl]   LeetCode failed: {exc}")

    if "github" not in payload and "leetcode" not in payload:
        print("[etl] nothing fetched — leaving the existing snapshot in place.")
        return 1

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        row = db.get(DashboardSnapshot, 1) or DashboardSnapshot(id=1)
        merged = dict(row.payload or {})
        merged.update(payload)  # keep the last-good half if one source failed now
        row.payload = merged
        row.generated_at = datetime.now(UTC)
        db.add(row)
        db.commit()
    print("[etl] snapshot stored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
