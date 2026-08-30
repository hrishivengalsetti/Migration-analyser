import pytest
from fastapi.testclient import TestClient
from main import app, DATA_DIR
import io
import os
import shutil
from database import DB_PATH, init_db, get_run, get_report

@pytest.fixture(autouse=True)
def clean_env():
    if DB_PATH.exists():
        os.remove(DB_PATH)
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    init_db()
    yield
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)

client = TestClient(app)

def test_pipeline_saves_report():
    original_file = ("original.zip", io.BytesIO(b"dummy original content"), "application/zip")
    migrated_file = ("migrated.zip", io.BytesIO(b"dummy migrated content"), "application/zip")
    
    response = client.post(
        "/api/runs",
        files={"original": original_file, "migrated": migrated_file}
    )
    
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    
    # Verify report was saved in DB
    report_db = get_report(run_id)
    assert report_db is not None
    assert report_db["run_id"] == run_id
    
    # Verify report API endpoint returns 200 and valid JSON
    report_resp = client.get(f"/api/runs/{run_id}/report")
    assert report_resp.status_code == 200
    assert "summary" in report_resp.json()
