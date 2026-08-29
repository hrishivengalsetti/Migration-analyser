# Migration Verifier — Architecture & Implementation Plan (Revised)

> **Role**: Senior Architect / Product Strategist  
> **Phase**: Implementation / Refinement
> **Goal**: Produce a plan specific enough that LatentCode can receive small, bounded tasks and execute them without architectural invention.

---

## 1. Precise Problem Statement

Software migrations (language upgrades, library replacements, framework changes, API refactors) introduce behavioral regressions that are invisible to the compiler and to existing tests. The failure mode is:

> "It compiles. Tests pass. We shipped. Something subtly broke."

The system must answer:

> **"Given a legacy codebase and a migrated codebase, what changed, what could break, and do we have deterministic evidence that the critical paths still behave equivalently?"**

The output is not an AI opinion. It is an evidence report backed by actual execution results, structured diffs, and reachability analysis.

---

## 2. MVP Definition (Aggressively Scoped)

### In Scope for MVP

| Area | What's In |
|---|---|
| Input | Zip file uploads for two versions: `original.zip` and `migrated.zip` |
| Language support | **Python only** |
| Analysis | File-level diff, function-level diff via AST parsing |
| Dependency graph | Intra-project import graph (no third-party traversal) |
| Blast radius | Transitive call/import reachability from changed symbols |
| Test selection | Map existing `pytest` tests → changed symbols via static analysis |
| Execution | Run test suite (old and new) inside Docker sandbox, capture pass/fail + stdout/stderr |
| Behavioral comparison | Deterministic: compare test results, captured outputs, exit codes |
| Report | Structured JSON evidence + rendered HTML/React page |
| AI role | Interpret migration intent, explain failures, classify risk |
| UI | Single-page React app: upload paths → view report |

### Explicitly Out of Scope (MVP)

| Feature | Reason Excluded |
|---|---|
| Multi-language support | Enormous complexity multiplication; Python alone is credible |
| Auto-generating new tests via AI | High failure risk, not core to value proposition |
| CI/CD integration | Not necessary for demo |
| Multi-user auth | Single-user local demo; SQLite is sufficient |
| Real-time streaming execution | Polling is fine for a demo |
| Third-party dependency analysis | Package diff is separate from code behavior |

---

## 3. Finalized Architectural Decisions

Based on initial discovery, the following open questions have been decided and locked in:

1. **AI Provider**: **Google Gemini Flash** via `google-generativeai` SDK. Fast, cheap, and ideal for hackathons.
2. **Demo Migration**: **Purpose-built Python project** with an intentional, realistic regression. This guarantees demo safety and predictability compared to fetching wild open-source repos.
3. **Frontend Input**: **Zip file upload** via `multipart/form-data`. Better UX, requires no direct host filesystem access from the server, easily deployable.
4. **Graph Visualization**: **React Flow**. It provides highly interactive, visually impressive node-edge diagrams out of the box.
5. **Call Graph Strategy**: **Best-effort static AST analysis only**. We accept Python's dynamic dispatch limitations. The UI will explicitly contain a disclaimer noting static boundaries.
6. **Code Parsing**: **Python `ast` stdlib** only. No Tree-sitter.
7. **Graph Storage**: **NetworkX** serialized to JSON (no heavy graph DB).
8. **Sandbox**: Pre-built Docker test image with read-only bind mounts.

---

## 4. Final MVP Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                  │
│                React + Vite + JS + Tailwind + shadcn              │
│                                                                   │
│   ┌──────────────┐   ┌───────────────────────────────────────┐   │
│   │  Upload Form  │   │         Report Viewer                  │   │
│   │ (.zip files)  │   │  Diff | Graph | Tests | Evidence | AI  │   │
│   └──────────────┘   └───────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              │ HTTP (Polling)
┌──────────────────────────────────────────────────────────────────┐
│                         BACKEND                                   │
│                     Python + FastAPI                              │
│                                                                   │
│  POST /api/runs        → Upload zips, fire BackgroundTask         │
│  GET  /api/runs/{id}   → Poll run status                          │
│  GET  /api/runs/{id}/report → Get full report                     │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   Analysis Pipeline                         │  │
│  │                                                             │  │
│  │  1. Diff Analyzer        (Python ast, difflib)              │  │
│  │  2. Graph Builder        (NetworkX)                         │  │
│  │  3. Blast Radius Engine  (NetworkX reachability)            │  │
│  │  4. Test Selector        (ast + pytest collection)          │  │
│  │  5. Sandbox Executor     (Docker SDK)                       │  │
│  │  6. Result Comparator    (deterministic)                    │  │
│  │  7. Evidence Collector   (structured records)               │  │
│  │  8. AI Interpreter       (LLM: intent + risk + narrative)   │  │
│  │  9. Report Assembler     (JSON → structured report)         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  SQLite (runs, evidence, reports)                                 │
│  NetworkX JSON (code graph, per run on disk)                      │
└──────────────────────────────────────────────────────────────────┘
                              │ Docker SDK
┌──────────────────────────────────────────────────────────────────┐
│                      SANDBOX LAYER                                │
│              Docker: python-test-runner image                     │
│   Read-only bind mounts | --network none | --memory 512m          │
│   Runs: pytest original/ and pytest migrated/ separately          │
│   Captures: JSON test results, stdout, stderr, exit code          │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Pipeline Error Handling & Resilience (CRITICAL)

Because analysis runs via FastAPI `BackgroundTasks`, any unhandled exception in the pipeline will crash the worker thread silently, leaving the database state as `analyzing` or `executing` forever. The frontend will poll infinitely.

**Rule**: The main pipeline orchestrator (`pipeline/runner.py`) MUST wrap the entire execution in a global `try/except Exception as e` block. On exception, it MUST call `update_run_status(run_id, "failed", str(e))` so the frontend can display the crash gracefully.

---

## 6. Data Model

### Run
```python
Run:
  id: UUID
  created_at: datetime
  status: "pending" | "analyzing" | "executing" | "interpreting" | "complete" | "failed"
  error: str | None
```
*(Other models: CodeGraph, Symbol, FileDiff, BlastRadius, TestResult, Evidence, AIInterpretation, Report remain unchanged from baseline).*

---

## 7. Classification Logic (Deterministic)

```text
IF regressions > 0:
    → "regression_detected"
ELSE IF tests_run == 0 OR all affected symbols have no_tests:
    → "unverified"
ELSE IF some affected symbols have no_tests:
    → "partially_verified"
ELSE:
    → "verified"
```

---

## 8. Agent Workflow & Hard Limits

### Execution Bot (LatentCode) Per-Task Workflow
1. Read `.agent/constitution.md`, `.agent/architecture.md`, `.agent/current-state.md`
2. Read assigned `TASK-NNN.md`
3. Explore ≤ 5 relevant files
4. Write implementation plan (inline in task file)
5. Request approval to exit plan mode (`plan_exit`).
6. Implement, run tests, debug (max 2 cycles).
7. Commit changes: `feat(TASK-NNN): <description>`
8. Update `.agent/current-state.md`

---

## 9. Milestones & Task Graph

### M1 — Backend Skeleton (In Progress)
- [x] TASK-001 FastAPI skeleton + SQLite schema + run CRUD
- [ ] TASK-002 BackgroundTask pipeline runner stub & Zip file saving
- [ ] TASK-003 Define Docker test runner image (Dockerfile)

### M2 — Diff & Graph Analysis
- [ ] TASK-004 Diff Analyzer: file-level & AST symbol diff (Python)
- [ ] TASK-005 Graph Builder: import/call graph from ast + Blast Radius

### M3 — Execution & Evidence
- [ ] TASK-006 Test Selector & Docker SDK execution
- [ ] TASK-007 Result Comparator & Evidence Collector

### M4 — AI & Reporting
- [ ] TASK-008 AI Interpreter (Gemini Flash integration)
- [ ] TASK-009 Report Assembler & API endpoint

### M5 — Frontend
- [ ] TASK-010 Frontend scaffold + Upload form
- [ ] TASK-011 Report viewer components (Diff, Graph, Tests, AI)

---

## 10. Testing Strategy Notes

### Testing BackgroundTasks
FastAPI's `TestClient` executes `BackgroundTasks` **synchronously** in the same thread *before* it returns the HTTP response.
- In production: `POST /api/runs` returns `status: "pending"` immediately.
- In `pytest` with `TestClient`: `POST /api/runs` will block until the background task finishes, and the response might still say `"pending"` (because it was generated before the task ran), but immediately querying the DB right after will yield `"complete"`.
- Tests must be written acknowledging this synchronous test-environment quirk, or we must use `httpx.AsyncClient` for true async testing.