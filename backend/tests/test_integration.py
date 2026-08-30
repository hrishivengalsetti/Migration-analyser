import io
import os
import json
import zipfile
import shutil
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app, DATA_DIR
import database
from database import DB_PATH, init_db, get_run, get_report

def is_docker_available() -> bool:
    try:
        import docker
        client = docker.from_env()
        return client.ping()
    except Exception:
        return False

DOCKER_AVAILABLE = is_docker_available()

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

def create_sample_zip(files: dict[str, str]) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for filename, content in files.items():
            z.writestr(filename, content)
    buf.seek(0)
    return buf

@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker daemon is not available or not running")
def test_full_pipeline_end_to_end():
    orig_zip = create_sample_zip({
        "app.py": "def calc(a, b):\n    return a + b\n",
        "test_app.py": "from app import calc\ndef test_calc():\n    assert calc(1, 2) == 3\n"
    })
    migr_zip = create_sample_zip({
        "app.py": "def calc(a, b):\n    return a + b  # optimized\n",
        "test_app.py": "from app import calc\ndef test_calc():\n    assert calc(1, 2) == 3\n"
    })

    res = client.post(
        "/api/runs",
        files={
            "original": ("orig.zip", orig_zip, "application/zip"),
            "migrated": ("migr.zip", migr_zip, "application/zip")
        }
    )
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    # Retrieve status
    status_res = client.get(f"/api/runs/{run_id}")
    assert status_res.status_code == 200
    run_data = status_res.json()
    assert run_data["status"] == "complete"
    assert run_data["error"] is None

    # Retrieve report
    report_res = client.get(f"/api/runs/{run_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()

    assert "classification" in report_data
    assert "summary" in report_data
    assert "file_diffs" in report_data
    assert "symbol_diffs" in report_data
    assert "evidence" in report_data
    assert len(report_data["file_diffs"]) > 0
    assert report_data["classification"] in ["verified", "partially_verified", "regression_detected", "unverified"]

def test_pipeline_handles_error_gracefully():
    # Submit invalid non-zip files
    invalid_orig = io.BytesIO(b"this is not a valid zip file content")
    invalid_migr = io.BytesIO(b"this is also not a valid zip file content")

    res = client.post(
        "/api/runs",
        files={
            "original": ("bad_orig.zip", invalid_orig, "application/zip"),
            "migrated": ("bad_migr.zip", invalid_migr, "application/zip")
        }
    )
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    run_db = get_run(run_id)
    assert run_db is not None
    assert run_db["status"] == "failed"
    assert run_db["error"] is not None
    assert run_db["status"] != "complete"

def test_pipeline_status_progression():
    orig_zip = create_sample_zip({"app.py": "def foo(): pass\n"})
    migr_zip = create_sample_zip({"app.py": "def foo(): return 1\n"})

    res = client.post(
        "/api/runs",
        files={
            "original": ("orig.zip", orig_zip, "application/zip"),
            "migrated": ("migr.zip", migr_zip, "application/zip")
        }
    )
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    run_db = get_run(run_id)
    assert run_db is not None
    assert run_db["status"] in ["complete", "failed"]
