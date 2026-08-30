import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Dummy Migration Verifier Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS: Dict[str, Dict[str, Any]] = {}


def build_report(run_id: str) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "classification": "needs_review",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_files_changed": 4,
            "total_symbols_changed": 6,
            "total_affected_symbols": 12,
            "regressions_count": 1,
            "total_tests_run": 8,
        },
        "ai_interpretation": {
            "migration_intent": "Refactor a legacy API response format to the newer typed schema while preserving compatibility.",
            "risk_summary": "The migration touches a shared API contract and one async call path, but the identified risk stays mostly localized to the request validation flow.",
            "key_concerns": [
                "The serializer now returns normalized field names that may affect downstream clients.",
                "One timeout-related regression was detected in the migrated code path.",
                "The call graph indicates a small blast radius around the request pipeline."
            ],
            "confidence": "medium",
        },
        "file_diffs": [
            {
                "file": "app/api.py",
                "status": "modified",
                "original_content": "def get_user(id):\n    return fetch_user(id)\n",
                "migrated_content": "def get_user(user_id):\n    return fetch_user(user_id)\n"
            },
            {
                "file": "app/client.py",
                "status": "modified",
                "original_content": "class HttpClient:\n    def post(self, url, payload):\n        return requests.post(url, json=payload)\n",
                "migrated_content": "class HttpClient:\n    def post(self, url, payload, timeout=10):\n        return requests.post(url, json=payload, timeout=timeout)\n"
            },
            {
                "file": "app/models.py",
                "status": "added",
                "original_content": "",
                "migrated_content": "class UserResponse:\n    id: str\n    name: str\n"
            }
        ],
        "symbol_diffs": [
            {
                "symbol_id": "app.api.get_user",
                "kind": "function",
                "change_kind": "parameter_rename",
                "file": "app/api.py",
                "line_original": 10,
                "line_migrated": 10,
                "original_source": "def get_user(id):\n    return fetch_user(id)\n",
                "migrated_source": "def get_user(user_id):\n    return fetch_user(user_id)\n"
            },
            {
                "symbol_id": "app.client.HttpClient.post",
                "kind": "method",
                "change_kind": "timeout_added",
                "file": "app/client.py",
                "line_original": 4,
                "line_migrated": 5,
                "original_source": "def post(self, url, payload):\n    return requests.post(url, json=payload)\n",
                "migrated_source": "def post(self, url, payload, timeout=10):\n    return requests.post(url, json=payload, timeout=timeout)\n"
            }
        ],
        "graph_data": {
            "nodes": [
                {"id": "app.api.get_user", "kind": "function", "file": "app/api.py"},
                {"id": "app.api.submit_order", "kind": "function", "file": "app/api.py"},
                {"id": "app.client.HttpClient.post", "kind": "method", "file": "app/client.py"},
                {"id": "app.views.checkout", "kind": "function", "file": "app/views.py"},
                {"id": "app.models.UserResponse", "kind": "class", "file": "app/models.py"}
            ],
            "edges": [
                {"source": "app.views.checkout", "target": "app.api.submit_order", "kind": "calls"},
                {"source": "app.api.submit_order", "target": "app.client.HttpClient.post", "kind": "calls"},
                {"source": "app.api.get_user", "target": "app.models.UserResponse", "kind": "returns"}
            ]
        },
        "blast_radius": {
            "changed_symbols": ["app.api.get_user", "app.client.HttpClient.post"],
            "directly_affected": ["app.api.submit_order", "app.api.get_user"],
            "transitively_affected": ["app.views.checkout", "app.models.UserResponse"]
        },
        "test_results": [
            {
                "test_id": "tests/test_api.py::test_get_user",
                "status_original": "passed",
                "status_migrated": "passed",
                "comparison": "passed_both"
            },
            {
                "test_id": "tests/test_api.py::test_submit_order",
                "status_original": "passed",
                "status_migrated": "passed",
                "comparison": "passed_both"
            },
            {
                "test_id": "tests/test_client.py::test_post_success",
                "status_original": "passed",
                "status_migrated": "passed",
                "comparison": "passed_both"
            },
            {
                "test_id": "tests/test_client.py::test_post_timeout",
                "status_original": "passed",
                "status_migrated": "failed",
                "comparison": "regression"
            },
            {
                "test_id": "tests/test_service.py::test_batch_sync",
                "status_original": "failed",
                "status_migrated": "failed",
                "comparison": "passed_both"
            },
            {
                "test_id": "tests/test_models.py::test_user_schema",
                "status_original": "passed",
                "status_migrated": "passed",
                "comparison": "passed_both"
            },
            {
                "test_id": "tests/test_auth.py::test_access_token",
                "status_original": "passed",
                "status_migrated": "passed",
                "comparison": "passed_both"
            },
            {
                "test_id": "tests/test_cache.py::test_invalidate_cache",
                "status_original": "passed",
                "status_migrated": "failed",
                "comparison": "regression"
            }
        ],
        "evidence": [
            {
                "symbol_id": "app.client.HttpClient.post",
                "file": "app/client.py",
                "change_kind": "timeout_added",
                "comparison": "regression",
                "passing_tests": ["tests/test_client.py::test_post_success"],
                "failing_tests": ["tests/test_client.py::test_post_timeout"]
            },
            {
                "symbol_id": "app.api.get_user",
                "file": "app/api.py",
                "change_kind": "parameter_rename",
                "comparison": "verified",
                "passing_tests": ["tests/test_api.py::test_get_user"],
                "failing_tests": []
            },
            {
                "symbol_id": "app.models.UserResponse",
                "file": "app/models.py",
                "change_kind": "new_model",
                "comparison": "improved",
                "passing_tests": ["tests/test_models.py::test_user_schema"],
                "failing_tests": []
            }
        ],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/runs")
async def create_run(original: UploadFile = File(...), migrated: UploadFile = File(...)):
    if not original.filename or not migrated.filename:
        raise HTTPException(status_code=400, detail="Both files are required.")

    run_id = f"dummy-{uuid.uuid4().hex[:8]}"
    RUNS[run_id] = {
        "run_id": run_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return {"run_id": run_id, "status": "pending"}


@app.get("/api/runs/{run_id}")
async def get_run_status(run_id: str):
    run = RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")

    # Simulate a realistic pipeline progression for the frontend poller.
    created = datetime.fromisoformat(run["created_at"])
    elapsed = (datetime.now(timezone.utc) - created).total_seconds()

    if elapsed < 1.5:
        status = "analyzing"
    elif elapsed < 3.0:
        status = "executing"
    else:
        status = "complete"

    run["status"] = status
    return {"run_id": run_id, "status": status}


@app.get("/api/runs/{run_id}/report")
async def get_run_report(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(status_code=404, detail="Run not found.")
    return build_report(run_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
