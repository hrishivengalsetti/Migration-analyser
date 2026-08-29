import pytest
from fastapi.testclient import TestClient
from main import app
import io
import os
import pytest
from fastapi.testclient import TestClient
from database import DB_PATH, init_db

# Delete DB before tests to ensure clean state
@pytest.fixture(autouse=True)
def clean_db():
    if DB_PATH.exists():
        os.remove(DB_PATH)
    init_db()  # Initialize the database explicitly for tests
    yield

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_run_success():
    # Mock zip files
    original_file = ("original.zip", io.BytesIO(b"dummy original content"), "application/zip")
    migrated_file = ("migrated.zip", io.BytesIO(b"dummy migrated content"), "application/zip")
    
    response = client.post(
        "/api/runs",
        files={"original": original_file, "migrated": migrated_file}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "pending"
    
    # Verify in DB via GET
    run_id = data["run_id"]
    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["run_id"] == run_id
    # TestClient runs background tasks synchronously, so it will actually be complete
    assert get_data["status"] == "complete"
    assert "created_at" in get_data
    assert get_data["error"] is None

def test_create_run_missing_file():
    original_file = ("original.zip", io.BytesIO(b"dummy original content"), "application/zip")
    
    # Missing migrated
    response = client.post(
        "/api/runs",
        files={"original": original_file}
    )
    
    assert response.status_code == 422 # FastAPI validation error for missing required field

def test_get_run_not_found():
    response = client.get("/api/runs/non-existent-id")
    assert response.status_code == 404
