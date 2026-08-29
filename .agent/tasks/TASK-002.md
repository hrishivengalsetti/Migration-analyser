# TASK-002: Pipeline Runner Stub + File Storage + BackgroundTask Wiring

**Milestone**: M1  
**Assigned to**: LatentCode  
**Status**: completed  
**Depends on**: TASK-001 (complete)  

---

## Goal

Wire the BackgroundTask pipeline runner into the `POST /api/runs` endpoint. When a run is created, the uploaded zip files should be saved to disk and a background task should be triggered. The pipeline runner itself is a stub — it updates the run status through stages but does not yet perform real analysis. This task establishes the plumbing.

---

## Context Files to Read

Before implementing, read these files IN ORDER:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `.agent/current-state.md`
4. `backend/main.py` (from TASK-001)
5. `backend/database.py` (from TASK-001)
6. This task file

---

## Inputs

- Completed TASK-001 backend scaffold

## Outputs

```
backend/
├── main.py              ← Updated: fires BackgroundTask, saves zip files
├── database.py          ← Updated: add update_run_status() function
├── pipeline/
│   ├── __init__.py
│   └── runner.py        ← Pipeline orchestrator stub
└── tests/
    └── test_runner.py   ← Tests for background task behavior
```

---

## Acceptance Criteria

### AC-1: File storage
- When `POST /api/runs` receives valid zips, both are saved to disk:
  - `backend/data/runs/{run_id}/original.zip`
  - `backend/data/runs/{run_id}/migrated.zip`
- The directory is created if it does not exist

### AC-2: BackgroundTask triggered
- After saving files, `POST /api/runs` fires a FastAPI `BackgroundTask` calling `run_pipeline(run_id)`
- The endpoint returns `{"run_id": ..., "status": "pending"}` immediately (does not wait for pipeline)

### AC-3: Pipeline runner stub & Global Error Handler
- `backend/pipeline/runner.py` contains `run_pipeline(run_id: str)` function
- The execution is wrapped in a top-level `try/except Exception as e` block. On exception, it calls `update_run_status(run_id, "failed", str(e))`.
- The stub:
  1. Updates run status to `"analyzing"` in SQLite
  2. Sleeps 1 second (simulating work)
  3. Updates run status to `"executing"`
  4. Sleeps 1 second
  5. Updates run status to `"complete"`
- This is a stub — no real analysis yet

### AC-4: Database update function
- `database.py` has `update_run_status(run_id: str, status: str, error: str | None = None)` function

### AC-5: Status polling works end-to-end
- After `POST /api/runs`, polling `GET /api/runs/{id}` eventually returns `"complete"`

### AC-6: All tests pass
- `cd backend && pytest tests/test_runner.py -v` exits with code 0

---

## Non-Goals

- Do NOT implement any real analysis logic
- Do NOT unzip the files yet (just save the zips)
- Do NOT implement any pipeline steps (diff, graph, etc.)
- Do NOT add a task queue (Celery, Redis, etc.) — use FastAPI BackgroundTasks only

---

## Technical Constraints

- FastAPI `BackgroundTasks` — not Celery, not threading.Thread directly
- File storage path: `backend/data/runs/{run_id}/`
- Status values must match the `RunStatus` enum from `models.py`

---

## Test Requirements

Write tests in `backend/tests/test_runner.py`:

1. Test that `POST /api/runs` saves both zip files to the correct paths
2. Test that after the background task completes, the run status is `"complete"`
   - Note: `TestClient` runs background tasks synchronously by default. Use this to verify status changes.
3. Test that `update_run_status()` correctly updates the run in SQLite

---

## Verification

```bash
cd backend && pytest tests/test_api.py tests/test_runner.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
