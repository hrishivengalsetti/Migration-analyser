import io
import os
import json
import zipfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app, DATA_DIR
import database
from database import DB_PATH, init_db, get_run, get_report
from models import AIInterpretation, RunStatus, Classification

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

@patch("brain.runner.generate_narrative")
@patch("brain.runner.run_tests_in_sandbox")
def test_pipeline_end_to_end_success(mock_sandbox, mock_groq):
    mock_sandbox.return_value = {
        "summary": {"passed": 1, "failed": 0, "error": 0, "total": 1},
        "tests": [{"nodeid": "test_app.test_calc", "outcome": "passed", "duration": 0.1}],
        "exit_code": 0,
        "stdout": "PASSED",
        "stderr": ""
    }
    mock_groq.return_value = AIInterpretation(
        migration_intent="Refactored calculator",
        risk_summary="Low risk",
        key_concerns=[],
        confidence="high"
    )

    orig_zip = create_sample_zip({
        "app.py": "def calc(a, b):\n    return a + b\n",
        "test_app.py": "from app import calc\ndef test_calc():\n    assert calc(1, 2) == 3\n"
    })
    migr_zip = create_sample_zip({
        "app.py": "def calc(a, b):\n    return a + b  # optimized\n",
        "test_app.py": "from app import calc\ndef test_calc():\n    assert calc(1, 2) == 3\n"
    })

    res = client.post("/api/runs", files={"original": ("orig.zip", orig_zip, "application/zip"), "migrated": ("migr.zip", migr_zip, "application/zip")})
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    run = get_run(run_id)
    assert run["status"] == "complete"
    assert run["error"] is None

    rep_db = get_report(run_id)
    assert rep_db is not None
    data = json.loads(rep_db["data"])
    assert data["classification"] == "verified"
    assert data["summary"]["total_files_changed"] == 1

@patch("brain.runner.generate_narrative")
@patch("brain.runner.run_tests_in_sandbox")
def test_pipeline_handles_empty_test_selection(mock_sandbox, mock_groq):
    mock_sandbox.return_value = {
        "summary": {"passed": 0, "failed": 0, "error": 0, "total": 0},
        "tests": [],
        "exit_code": 0,
        "stdout": "No tests selected.",
        "stderr": ""
    }
    mock_groq.return_value = AIInterpretation(
        migration_intent="No tests run",
        risk_summary="Unverified",
        key_concerns=[],
        confidence="none"
    )

    orig_zip = create_sample_zip({"app.py": "def foo(): pass\n"})
    migr_zip = create_sample_zip({"app.py": "def foo(): return 1\n"})

    res = client.post("/api/runs", files={"original": ("orig.zip", orig_zip, "application/zip"), "migrated": ("migr.zip", migr_zip, "application/zip")})
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    run = get_run(run_id)
    assert run["status"] == "complete"

    rep_db = get_report(run_id)
    assert rep_db is not None
    data = json.loads(rep_db["data"])
    assert data["classification"] == "unverified"

@patch("brain.runner._extract_zip")
def test_pipeline_fatal_error_sets_failed_status(mock_extract):
    mock_extract.side_effect = RuntimeError("Extraction failed due to corrupted zip")

    orig_zip = create_sample_zip({"app.py": "pass"})
    migr_zip = create_sample_zip({"app.py": "pass"})

    res = client.post("/api/runs", files={"original": ("orig.zip", orig_zip, "application/zip"), "migrated": ("migr.zip", migr_zip, "application/zip")})
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    run = get_run(run_id)
    assert run["status"] == "failed"
    assert "Extraction failed" in run["error"]

@patch("brain.runner.generate_narrative")
@patch("brain.runner.run_tests_in_sandbox")
def test_pipeline_handles_docker_and_groq_failures(mock_sandbox, mock_groq):
    mock_sandbox.return_value = {
        "summary": {"passed": 1, "failed": 0, "error": 1, "total": 2},
        "tests": [
            {"nodeid": "test_app.test_calc1", "outcome": "passed", "duration": 0.1},
            {"nodeid": "test_app.test_calc2", "outcome": "error", "duration": 0.0}
        ],
        "exit_code": 0,
        "stdout": "",
        "stderr": "Container execution timed out"
    }
    mock_groq.return_value = AIInterpretation(
        migration_intent="Unknown",
        risk_summary="Failed to generate AI summary",
        key_concerns=["AI interpretation failed."],
        confidence="none"
    )

    orig_zip = create_sample_zip({
        "app.py": "def calc1(): return 1\ndef calc2(): return 2\n",
        "test_app.py": "from app import calc1, calc2\ndef test_calc1(): assert calc1() == 1\ndef test_calc2(): assert calc2() == 2\n"
    })
    migr_zip = create_sample_zip({
        "app.py": "def calc1(): return 10\ndef calc2(): return 20\n",
        "test_app.py": "from app import calc1, calc2\ndef test_calc1(): assert calc1() == 1\ndef test_calc2(): assert calc2() == 2\n"
    })

    res = client.post("/api/runs", files={"original": ("orig.zip", orig_zip, "application/zip"), "migrated": ("migr.zip", migr_zip, "application/zip")})
    assert res.status_code == 200
    run_id = res.json()["run_id"]

    run = get_run(run_id)
    assert run["status"] == "complete"

    rep_db = get_report(run_id)
    assert rep_db is not None
    data = json.loads(rep_db["data"])
    assert data["classification"] == "partially_verified"
