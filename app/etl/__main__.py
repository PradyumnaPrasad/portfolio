"""Run the GitHub ETL and store the snapshot.

python -m app.etl            # uses GITHUB_USERNAME or "PradyumnaPrasad"
python -m app.etl someuser
"""

from __future__ import annotations

import os
import sys

from app.db import SessionLocal, engine
from app.etl.github import fetch_snapshot
from app.models import Base, DashboardSnapshot


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    username = argv[0] if argv else os.getenv("GITHUB_USERNAME", "PradyumnaPrasad")

    print(f"[etl] fetching GitHub activity for {username} ...")
    snap = fetch_snapshot(username)
    print(
        f"[etl] {snap['repo_count']} repos · {snap['star_count']} stars · "
        f"{len(snap['languages'])} languages · calendar via {snap['calendar_source']}"
    )

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        row = db.get(DashboardSnapshot, 1) or DashboardSnapshot(id=1)
        row.payload = snap
        from datetime import UTC, datetime

        row.generated_at = datetime.now(UTC)
        db.add(row)
        db.commit()
    print("[etl] snapshot stored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
