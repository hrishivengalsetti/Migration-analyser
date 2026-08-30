import pytest
from database import DB_PATH, init_db, create_run, get_run_paths, get_db_connection

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield

def test_get_run_paths_success():
    run_id = "test-run-paths-123"
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO runs (id, created_at, status, original_path, migrated_path) VALUES (?, ?, ?, ?, ?)",
            (run_id, "2026-08-30T00:00:00Z", "pending", "/data/runs/test/original.zip", "/data/runs/test/migrated.zip")
        )
        conn.commit()
    finally:
        conn.close()

    orig, migr = get_run_paths(run_id)
    assert orig == "/data/runs/test/original.zip"
    assert migr == "/data/runs/test/migrated.zip"

def test_get_run_paths_missing():
    with pytest.raises(ValueError):
        get_run_paths("non-existent-run")
