import pytest
from fastapi.testclient import TestClient
from main import app
import io
import os
import json
from database import DB_PATH, init_db, save_report

@pytest.fixture(autouse=True)
def clean_db():
    if DB_PATH.exists():
        os.remove(DB_PATH)
    init_db()
    yield

client = TestClient(app)

def test_get_report_not_found():
    response = client.get("/api/runs/non-existent-id/report")
    assert response.status_code == 404

def test_get_report_success():
    # Insert run
    original_file = ("original.zip", io.BytesIO(b"dummy original content"), "application/zip")
    migrated_file = ("migrated.zip", io.BytesIO(b"dummy migrated content"), "application/zip")
    
    post_resp = client.post(
        "/api/runs",
        files={"original": original_file, "migrated": migrated_file}
    )
    run_id = post_resp.json()["run_id"]
    
    # Save dummy report
    save_report(run_id, json.dumps({"test": "data", "summary": {"total_files_changed": 5}}), "2026-08-30T00:00:00Z")
    
    get_resp = client.get(f"/api/runs/{run_id}/report")
    assert get_resp.status_code == 200
    res_data = get_resp.json()
    assert res_data["run_id"] == run_id
    assert res_data["test"] == "data"
    assert res_data["summary"]["total_files_changed"] == 5
