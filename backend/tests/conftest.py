import os
import time
import pytest

from fastapi.testclient import TestClient

os.environ.setdefault("DB_URL", os.getenv("DB_URL", "postgresql://postgres:postgres@postgres:5432/s2x"))

from app.main import app  # noqa: E402
from app.db_pool import get_conn  # noqa: E402


@pytest.fixture(scope="session")
def client():
    deadline = time.time() + 15
    last_err = None
    while time.time() < deadline:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("select 1;")
                _ = cur.fetchone()
                break
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    if last_err:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("select 1;")
            _ = cur.fetchone()
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE notifications RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE notification_subscriptions RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE shares RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE transcription_artifacts RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE segments RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE transcriptions RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE audio_files RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE projects RESTART IDENTITY CASCADE;")
        cur.execute("TRUNCATE users RESTART IDENTITY CASCADE;")
        conn.commit()
    yield

