# TASK-010B: Report Assembler & Storage

**Milestone**: M6  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-010A (complete)  

---

## Goal

Implement the report assembler that combines all pipeline outputs (file diffs, symbol diffs, blast radius, test results, evidence, classification, and AI interpretation) into a single structured `Report` JSON object. Persist the report to SQLite and expose it via a REST API endpoint `GET /api/runs/{run_id}/report`.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/database.py`
4. `backend/models.py`
5. This task file

---

## Inputs

- All pipeline stage outputs assembled into a Report model

## Outputs

```
backend/pipeline/report.py      ← New file
backend/database.py              ← Updated: add save_report() and get_report()
backend/main.py                  ← Updated: add GET /api/runs/{run_id}/report endpoint
backend/models.py                ← Updated: add Report model
backend/tests/test_report.py    ← New file
```

---

## Data Models (add to models.py)

```python
class Report(BaseModel):
    run_id: str
    classification: Classification
    summary: dict  # {"files_changed": int, "symbols_changed": int, "blast_radius_count": int, "regressions": int, "tests_run": int}
    file_diffs: list[FileDiff]
    symbol_diffs: list[SymbolDiff]
    blast_radius: BlastRadius
    test_results_original: dict   # raw sandbox output for original
    test_results_migrated: dict   # raw sandbox output for migrated
    comparisons: list[dict]       # per-test comparisons
    evidence: list[Evidence]
    ai_interpretation: Optional[AIInterpretation] = None
    graph_data: Optional[dict] = None  # NetworkX node_link_data for frontend graph rendering
```

---

## Acceptance Criteria

### AC-1: Report assembly function signature
```python
def assemble_report(
    run_id: str,
    file_diffs: list[FileDiff],
    symbol_diffs: list[SymbolDiff],
    blast_radius: BlastRadius,
    test_results_original: dict,
    test_results_migrated: dict,
    comparisons: list[dict],
    evidence: list[Evidence],
    classification: Classification,
    ai_interpretation: Optional[AIInterpretation],
    graph_data: Optional[dict] = None,
) -> Report:
    ...
```

### AC-2: Summary computation
- The `summary` dict must be computed from the inputs:
  - `files_changed`: count of file diffs with status != "unchanged"
  - `symbols_changed`: length of `symbol_diffs`
  - `blast_radius_count`: `blast_radius.total_affected_count`
  - `regressions`: count of comparisons with `comparison="regression"`
  - `tests_run`: total number of tests in migrated results

### AC-3: Database storage
- `save_report(run_id: str, report: Report)` in `database.py`:
  - Inserts into `reports` table: `run_id`, `data` (JSON string via `report.model_dump_json()`), `generated_at` (ISO timestamp)
  - Uses `INSERT OR REPLACE` to handle re-runs
- `get_report(run_id: str) -> dict | None` in `database.py`:
  - Queries `reports` table by `run_id`
  - Returns parsed JSON dict or `None` if not found

### AC-4: API endpoint
- `GET /api/runs/{run_id}/report`:
  - Returns the full Report JSON when the run is complete and report exists
  - Returns HTTP 404 with `{"detail": "Report not found"}` if:
    - The run_id does not exist, OR
    - The report has not been generated yet
  - Returns HTTP 200 with the full Report JSON object on success

### AC-5: Report is valid JSON
- `Report.model_dump()` produces a valid JSON-serializable dict
- All nested Pydantic models serialize correctly

### AC-6: All tests pass
- `cd backend && pytest tests/test_report.py -v` exits with code 0

---

## Non-Goals

- Do NOT implement the AI interpreter (that is TASK-011)
- Do NOT wire into the pipeline runner (that is TASK-012)
- Do NOT implement report rendering / HTML generation
- Do NOT implement report caching beyond SQLite storage

---

## Technical Constraints

- Use raw `sqlite3` for database operations (no ORM)
- Use Pydantic `model_dump_json()` for serialization
- Use `json.loads()` for deserialization from DB
- Report endpoint must be added to the FastAPI app in `main.py`

---

## Test Requirements

Write tests in `backend/tests/test_report.py`:

1. `test_assemble_report_basic` — assemble a report with minimal inputs → Report model is valid
2. `test_summary_computation` — verify summary counts are correctly computed from inputs
3. `test_save_and_get_report` — save a report to DB and retrieve it → data matches
4. `test_get_report_not_found` — query non-existent run_id → returns None
5. `test_report_endpoint_returns_report` — `GET /api/runs/{id}/report` with saved report → 200 + correct JSON
6. `test_report_endpoint_not_found` — `GET /api/runs/{id}/report` with no report → 404
7. `test_report_serialization_roundtrip` — `Report.model_dump_json()` → `json.loads()` → valid dict

---

## Verification

```bash
cd backend && pytest tests/test_report.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
