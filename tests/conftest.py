import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.gettempdir()) / "portfolio_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    _TMP.unlink(missing_ok=True)
    with TestClient(app) as c:  # runs lifespan: create_all + seed
        yield c
    _TMP.unlink(missing_ok=True)


@pytest.fixture
def db():
    from app.db import SessionLocal

    with SessionLocal() as s:
        yield s
