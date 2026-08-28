# Milestones

## M0 — Project Foundation ✅
**Owner**: Planning Bot (Antigravity)
**Status**: Complete

- .agent/ structure created
- constitution.md, problem.md, architecture.md, decisions.md, milestones.md written
- task-graph.json created
- First task wave (TASK-001 to TASK-010) written
- Skills written

---

## M1 — Backend Skeleton
**Owner**: LatentCode  
**Tasks**: TASK-001, TASK-002  
**Status**: Pending

Deliverables:
- FastAPI app with CORS configured for frontend dev
- SQLite schema (runs, reports tables)
- `POST /api/runs` — creates run record, fires BackgroundTask
- `GET /api/runs/{id}` — returns run status
- Pipeline runner stub (logs steps but does nothing yet)
- `pytest tests/test_api.py` passes

---

## M2 — Diff Analyzer
**Owner**: LatentCode  
**Tasks**: TASK-003, TASK-004  
**Status**: Pending

Deliverables:
- File-level diff: detect added/deleted/modified/renamed files
- AST-level symbol diff: which functions/classes changed, how
- `pytest tests/test_diff_analyzer.py` passes

---

## M3 — Code Graph + Blast Radius
**Owner**: LatentCode  
**Tasks**: TASK-005, TASK-006  
**Status**: Pending

Deliverables:
- NetworkX graph built from `ast` walk of Python codebase
- Import edges + call edges
- Blast radius: transitive reachability from changed symbols
- Graph serialized to JSON per run
- `pytest tests/test_graph_builder.py tests/test_blast_radius.py` passes

---

## M4 — Test Selection
**Owner**: LatentCode  
**Tasks**: TASK-007  
**Status**: Pending

Deliverables:
- Map test functions → symbols they exercise (via import + call analysis)
- Filter to tests relevant to blast radius
- `pytest tests/test_test_selector.py` passes

---

## M5 — Sandbox Executor
**Owner**: LatentCode  
**Tasks**: TASK-008  
**Status**: Pending

Deliverables:
- Docker image built: `migration-verifier-runner:latest`
- Docker SDK integration: run pytest in container, capture JSON results
- `TestResult` records produced
- `pytest tests/test_sandbox.py` passes (with mock Docker or real Docker)

---

## M6 — Evidence + Classification
**Owner**: LatentCode  
**Tasks**: TASK-009, TASK-010  
**Status**: Pending

Deliverables:
- Deterministic behavioral comparison: per-test regression/improvement/equivalent
- Evidence assembly: per-symbol evidence records
- Classification logic: verified/partially_verified/regression_detected/unverified
- Report assembly
- `GET /api/runs/{id}/report` returns full Report JSON
- `pytest tests/test_comparator.py tests/test_evidence.py` passes

---

## M7 — AI Interpreter
**Owner**: LatentCode  
**Tasks**: TASK-011  
**Status**: Pending

Deliverables:
- Gemini Flash integration
- Prompt template in `backend/pipeline/prompts/interpreter.txt`
- `AIInterpretation` returned and included in report
- Graceful fallback if `GEMINI_API_KEY` not set
- `pytest tests/test_interpreter.py` passes (with mocked API)

---

## M8 — Full Pipeline Integration
**Owner**: LatentCode  
**Tasks**: TASK-012  
**Status**: Pending

Deliverables:
- All pipeline steps wired into `runner.py`
- End-to-end test: submit demo migration, get full report
- `pytest tests/test_integration.py` passes

---

## M9 — Frontend
**Owner**: LatentCode  
**Tasks**: TASK-013, TASK-014, TASK-015, TASK-016, TASK-017  
**Status**: Pending

Deliverables:
- Vite + React + Tailwind + shadcn scaffold
- Upload page: two zip inputs + Analyze button + status polling
- Report page: 5 tabs (Summary, Changes, Impact, Tests, Evidence)
- React Flow blast radius graph
- Smoke test: Playwright navigates to upload page and verifies it loads

---

## M10 — Demo Polish
**Owner**: Planning Bot + LatentCode  
**Tasks**: TASK-018, TASK-019  
**Status**: Pending

Deliverables:
- `demo/original/` and `demo/migrated/` — purpose-built Python project with controlled regression
- README with demo instructions
- Docker image pre-built and tested
- End-to-end demo walkthrough document
