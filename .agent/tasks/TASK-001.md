# TASK-001: Backend Project Scaffold

**Milestone**: M1  
**Assigned to**: LatentCode  
**Status**: completed  
**Depends on**: none  

---

## Goal

Create the complete backend project structure: FastAPI application, SQLite database schema and connection, Pydantic data models, and CRUD endpoints for analysis runs. The backend should be runnable with `uvicorn` and all acceptance tests should pass.

---

## Context Files to Read

Before implementing, read these files IN ORDER:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `.agent/current-state.md`
4. This task file

Do not read any other files before starting.

---

## Inputs

- Empty `backend/` directory (to be created)

## Outputs

A working FastAPI backend with:

```
backend/
├── main.py              ← FastAPI app, CORS, routers
├── database.py          ← SQLite connection, table creation, run CRUD
├── models.py            ← Pydantic models for Run, RunStatus, CreateRunResponse
├── requirements.txt     ← All Python dependencies
└── tests/
    ├── __init__.py
    └── test_api.py      ← API endpoint tests
```

---

## Acceptance Criteria

### AC-1: Project structure exists
- `backend/main.py` exists and imports without error
- `backend/database.py` exists and imports without error
- `backend/models.py` exists and imports without error
- `backend/requirements.txt` exists

### AC-2: SQLite schema
- Running the app creates a SQLite database file `backend/data/runs.db`
- The database has a `runs` table with columns: `id` (TEXT PK), `created_at` (TEXT), `status` (TEXT), `original_path` (TEXT NULLABLE), `migrated_path` (TEXT NULLABLE), `error` (TEXT NULLABLE)
- The database has a `reports` table with columns: `run_id` (TEXT PK, FK→runs.id), `data` (TEXT), `generated_at` (TEXT)

### AC-3: POST /api/runs endpoint
- Accepts `multipart/form-data` with fields:
  - `original`: zip file (required)
  - `migrated`: zip file (required)
- Creates a run record in SQLite with status `"pending"`
- Returns `{"run_id": "<uuid>", "status": "pending"}`
- Does NOT yet fire a background task (that is TASK-002)
- Returns 400 if either zip is missing

### AC-4: GET /api/runs/{run_id} endpoint
- Returns `{"run_id": ..., "status": ..., "created_at": ..., "error": null}` for an existing run
- Returns 404 if run does not exist

### AC-5: CORS
- CORS is configured to allow `http://localhost:5173` (Vite dev server)

### AC-6: Health check
- `GET /health` returns `{"status": "ok"}`

### AC-7: All tests pass
- `cd backend && pytest tests/test_api.py -v` exits with code 0

---

## Non-Goals

- Do NOT implement any pipeline logic
- Do NOT fire a BackgroundTask yet (that is TASK-002)
- Do NOT unzip the uploaded files yet (that is TASK-002)
- Do NOT implement the report endpoint (that is later)
- Do NOT use SQLAlchemy or any ORM — use raw `sqlite3`
- Do NOT add authentication

---

## Technical Constraints

- Python 3.11
- FastAPI
- Pydantic v2
- `sqlite3` (stdlib) — no SQLAlchemy
- `python-multipart` for file upload parsing
- `uvicorn` for running the server
- `pytest` + `httpx` for testing (use `TestClient` from `fastapi.testclient`)
- All dependencies in `requirements.txt`

---

## Key Design Notes

### Database initialization

The database should be created at startup using FastAPI's `lifespan` context:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)
```

### Run ID

Use `uuid.uuid4()` to generate run IDs. Store as string.

### File storage

For AC-3, just receive the zip files and verify they are valid. Do not save them to disk yet.
In TASK-002, we will save them to `backend/data/runs/{run_id}/original.zip` and `backend/data/runs/{run_id}/migrated.zip`.

### Pydantic models

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RunStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    INTERPRETING = "interpreting"
    COMPLETE = "complete"
    FAILED = "failed"

class Run(BaseModel):
    run_id: str
    status: RunStatus
    created_at: str
    error: Optional[str] = None

class CreateRunResponse(BaseModel):
    run_id: str
    status: str
```

---

## Test Requirements

Write tests in `backend/tests/test_api.py` covering:

1. `POST /api/runs` with valid zips → 200, run_id returned, run in DB
2. `POST /api/runs` missing one file → 400
3. `GET /api/runs/{id}` for existing run → 200, correct status
4. `GET /api/runs/{id}` for non-existent run → 404
5. `GET /health` → 200, `{"status": "ok"}`

Use `TestClient` from `fastapi.testclient`. Use `io.BytesIO` to create mock zip files in tests.

---

## Verification

```bash
cd backend && pip install -r requirements.txt && pytest tests/test_api.py -v
```

All tests must pass. No warnings-as-errors.

---

## Blocker Section

*(LatentCode fills this in if blocked)*

Blocker: N/A  
Attempts made: N/A  
Error output: N/A  

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
