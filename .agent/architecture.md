# Technical Architecture

## Repository Structure

```
hackathon/
├── .agent/                  ← Project memory & governance
├── backend/                 ← Python + FastAPI
│   ├── main.py              ← FastAPI app, CORS, routers, lifespan
│   ├── models.py            ← Pydantic models + SQLite schemas / enums
│   ├── database.py          ← SQLite connection + queries (raw sqlite3)
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── runner.py        ← Pipeline orchestrator (BackgroundTask + try/except)
│   │   ├── diff_analyzer.py ← File + AST symbol diff
│   │   ├── graph_builder.py ← NetworkX graph from ast
│   │   ├── blast_radius.py  ← Graph reachability (nx.ancestors)
│   │   ├── test_selector.py ← Symbol-to-test mapping (ast + pytest collection)
│   │   ├── sandbox.py       ← Docker SDK execution
│   │   ├── comparator.py    ← Deterministic result comparison
│   │   ├── evidence.py      ← Evidence assembly
│   │   ├── interpreter.py   ← Gemini Flash LLM call (via google-generativeai)
│   │   └── report.py        ← Report assembly + classification
│   ├── prompts/
│   │   └── interpreter.txt  ← Version-controlled LLM prompt template
│   ├── data/                ← SQLite db + file storage per run
│   ├── requirements.txt
│   └── tests/
│       ├── test_api.py
│       ├── test_runner.py
│       ├── test_diff_analyzer.py
│       ├── test_graph_builder.py
│       ├── test_blast_radius.py
│       ├── test_test_selector.py
│       ├── test_sandbox.py
│       ├── test_comparator.py
│       ├── test_evidence.py
│       ├── test_interpreter.py
│       └── test_integration.py
├── frontend/                ← React + Vite + JS + Tailwind + shadcn
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx
│   │   │   └── ReportPage.jsx
│   │   └── components/
│   │       ├── DiffViewer.jsx
│   │       ├── GraphView.jsx      ← React Flow
│   │       ├── TestResults.jsx
│   │       ├── EvidencePanel.jsx
│   │       └── AINarrative.jsx
│   ├── package.json
│   └── vite.config.js
├── docker/
│   └── test-runner/
│       ├── Dockerfile
│       └── requirements.txt ← pytest, pytest-json-report
├── demo/
│   ├── original/            ← Demo migration: original Python project
│   ├── migrated/            ← Demo migration: migrated Python project (with regression)
│   └── README.md
├── architecture-revised.md  ← Historical reference doc (retained for context)
└── README.md
```

---

## 1. Precise Problem Statement & Scope

**Problem**: Migrations introduce silent behavioral regressions.  
**System Question**: *"Given a legacy codebase and a migrated codebase, what changed, what could break, and do we have deterministic evidence that critical paths still behave equivalently?"*

### MVP Scope (Aggressively Scoped)

| Feature / Area | In Scope | Excluded from MVP |
|---|---|---|
| **Input** | Zip uploads (`original.zip`, `migrated.zip`) via `multipart/form-data` | Direct filesystem paths, Git repos, streaming tarballs |
| **Language** | **Python only** | Multi-language, cross-language bridges |
| **Parsing** | Python `ast` stdlib | Tree-sitter, libcst, C extensions |
| **Diff** | File-level diff + AST symbol diff | Line/hunk diffs, syntax-tree tree-diffs |
| **Dependency Graph** | Intra-project NetworkX graph (import + call edges) | Third-party dependency traversal, dynamic call graphs |
| **Blast Radius** | Transitive call/import reachability (`nx.ancestors`) | Dynamic tracing, impact probability scoring |
| **Test Selection** | Static mapping of `pytest` tests to changed symbols | Dynamic coverage, AI test generation |
| **Execution Sandbox** | Docker container (`python-test-runner`), read-only bind mounts, `--network none`, `--memory 512m` | Bare host execution, virtualenv isolation, gVisor |
| **Comparison** | Deterministic result comparison (pass/fail, stdout, exit codes) | Fuzzy AI output matching |
| **AI Role** | Single call to Google Gemini Flash for narrative interpretation | Primary evidence generation, automated fixes, test writing |
| **UI** | React single-page application (Upload page + Report viewer) | Multi-user authentication, persistent team workspaces |

---

## 2. Backend Architecture: Python + FastAPI

### API Endpoints

```
POST /api/runs
  Body: multipart/form-data { original: <zip file>, migrated: <zip file> }
  Response: { run_id: UUID (string), status: "pending" }

GET /api/runs/{run_id}
  Response: { run_id: str, status: RunStatus, created_at: str, error: Optional[str] }

GET /api/runs/{run_id}/report
  Response: Report (Full structured JSON object)
```

### Pipeline Execution & Worker Resilience

1. `POST /api/runs` validates uploaded zip files, saves them to disk (`backend/data/runs/{run_id}/original.zip` and `migrated.zip`), creates a `Run` record with status `"pending"`, and dispatches a FastAPI `BackgroundTask` for `run_pipeline(run_id)`.
2. `run_pipeline` in `backend/pipeline/runner.py` **MUST** wrap the entire execution in a global `try/except Exception as e` block.
3. On any failure, `update_run_status(run_id, "failed", str(e))` is called to ensure the database record reflects the error and prevents infinite polling by the frontend.
4. On success, run status progresses through: `"pending"` → `"analyzing"` → `"executing"` → `"interpreting"` → `"complete"`.

### Pipeline Steps (Sequential Execution)

1. **DiffAnalyzer** (`diff_analyzer.py`): Computes file status (ADDED, DELETED, MODIFIED) and AST symbol diffs (`SymbolDiff`).
2. **GraphBuilder** (`graph_builder.py`): Builds intra-project NetworkX directed call/import graphs for original and migrated codebases.
3. **BlastRadius** (`blast_radius.py`): Calculates direct and transitive reachability from changed symbols using `nx.ancestors()`.
4. **TestSelector** (`test_selector.py`): Maps `pytest` test functions to changed and affected symbols using AST static analysis.
5. **SandboxExecutor** (`sandbox.py`): Runs `pytest` with `pytest-json-report` in isolated Docker containers for both original and migrated code.
6. **Comparator** (`comparator.py`): Compares test results deterministically (passed, failed, regressed, improved).
7. **EvidenceCollector** (`evidence.py`): Assembles per-symbol evidence cards linking diffs, blast radius, and test execution results.
8. **Interpreter** (`interpreter.py`): Invokes Google Gemini Flash (`google-generativeai` SDK) exactly once per run to generate migration intent, risk summary, and key concerns. Falls back gracefully if `GEMINI_API_KEY` is not set.
9. **ReportAssembler** (`report.py`): Assembles full structured `Report` JSON and computes final deterministic classification.

---

## 3. Data Model & Database (SQLite + JSON)

### Database: SQLite (`sqlite3` stdlib, no ORM)

Located at `backend/data/runs.db`.

```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,      -- "pending", "analyzing", "executing", "interpreting", "complete", "failed"
    original_path TEXT,
    migrated_path TEXT,
    error TEXT
);

CREATE TABLE reports (
    run_id TEXT PRIMARY KEY,
    data TEXT NOT NULL,        -- Full JSON blob of the Report model
    generated_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
```

### File-Based Persistence

- NetworkX Code Graphs: Saved as JSON per run at `backend/data/runs/{run_id}/graph_original.json` and `graph_migrated.json` using `nx.node_link_data()`.
- Unzipped Codebases: Extracted to `backend/data/runs/{run_id}/original/` and `backend/data/runs/{run_id}/migrated/`.

### Core Data Models (Pydantic v2)

```python
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

class FileStatus(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"

class FileDiff(BaseModel):
    file: str
    status: FileStatus
    original_content: Optional[str] = None
    migrated_content: Optional[str] = None

class SymbolKind(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"

class SymbolChangeKind(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    BODY_CHANGED = "body_changed"
    SIGNATURE_CHANGED = "signature_changed"

class SymbolDiff(BaseModel):
    symbol_id: str  # e.g., "mypackage.module.ClassName.method_name"
    file: str
    kind: SymbolKind
    change_kind: SymbolChangeKind
    original_source: Optional[str] = None
    migrated_source: Optional[str] = None
    line_original: Optional[int] = None
    line_migrated: Optional[int] = None

class BlastRadius(BaseModel):
    changed_symbols: list[str]
    directly_affected: list[str]
    transitively_affected: list[str]
    all_affected: list[str]
    cycles_detected: bool
    total_affected_count: int

class Evidence(BaseModel):
    symbol_id: str
    file: str
    change_kind: Optional[SymbolChangeKind] = None
    comparison: str  # "verified", "regression", "improved", "no_tests"
    failing_tests: list[str] = []
    passing_tests: list[str] = []

class AIInterpretation(BaseModel):
    migration_intent: str
    risk_summary: str
    key_concerns: list[str]
    confidence: str

class Classification(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    REGRESSION_DETECTED = "regression_detected"
    UNVERIFIED = "unverified"
```

---

## 4. Classification Logic (Deterministic)

The overall migration classification is strictly deterministic and computed directly from collected evidence and test execution counts:

```python
def classify(evidence: list[Evidence], tests_run: int) -> Classification:
    regressions = sum(1 for e in evidence if e.comparison == "regression")
    no_tests = sum(1 for e in evidence if e.comparison == "no_tests")

    if regressions > 0:
        return Classification.REGRESSION_DETECTED
    elif tests_run == 0 or no_tests == len(evidence):
        return Classification.UNVERIFIED
    elif no_tests > 0:
        return Classification.PARTIALLY_VERIFIED
    else:
        return Classification.VERIFIED
```

*Note: AI interpretation NEVER overrides or modifies this classification.*

---

## 5. Code Graph & Blast Radius Engine (NetworkX)

- **Nodes**: Symbols with ID `<module>.<symbol>`, attributes: `kind`, `file`, `line_start`, `line_end`.
- **Edges**: `kind="imports"` or `kind="calls"`.
- **Reachability Algorithm**: `nx.ancestors(G, target_symbol)` finds all upstream caller/importer nodes that have a directed path to `target_symbol`.
- **Disclaimer**: Static AST resolution cannot handle Python's dynamic dispatch or `getattr()`. The UI displays an explicit disclaimer noting static analysis boundaries.

---

## 6. Sandboxed Execution (Docker)

- **Image**: Pre-built Docker image `migration-verifier-runner:latest` (built from `docker/test-runner/Dockerfile`).
- **Container Configuration**:
  - Read-only bind mounts: `/workspace` bound to `code_path` (`mode: "ro"`).
  - Security / Resource Limits: `network_disabled=True`, `mem_limit="512m"`, `nano_cpus=1_000_000_000`, `pids_limit=100`, `user="nobody"`.
  - Execution Command: `pytest /workspace --json-report --json-report-file=/tmp/results.json -q`
  - Output Capture: Parsed JSON report from container + stdout/stderr/exit code.

---

## 7. AI Interpretation (Google Gemini Flash)

- **SDK**: `google-generativeai`
- **Trigger**: Single API call per run at the end of evidence collection.
- **Input**: Summary JSON containing changed files, changed symbols, blast radius size, regressions count, and evidence summary.
- **Prompt**: Loaded from `backend/prompts/interpreter.txt`.
- **Fallback**: If `GEMINI_API_KEY` is missing or the call fails, populate `AIInterpretation` with default "AI interpretation unavailable" fallback fields without crashing the pipeline.

---

## 8. Frontend Architecture: React + Vite + JS + Tailwind + shadcn

- **Stack**: Vite + React (JavaScript) + Tailwind CSS + shadcn/ui primitives.
- **Graph Visualizer**: React Flow for node-edge blast radius diagrams.
- **Pages**:
  1. `UploadPage.jsx`: Drag-and-drop zip file inputs for `original.zip` and `migrated.zip`, trigger submit, and display polling status progress bar.
  2. `ReportPage.jsx`: Tabbed report viewer displaying:
     - **Summary Tab**: Classification status badge, execution summary, AI narrative card.
     - **Changes Tab**: Side-by-side file and symbol diffs.
     - **Impact Tab**: Interactive React Flow blast radius node graph.
     - **Tests Tab**: Table of pytest results comparing original vs migrated runs.
     - **Evidence Tab**: Per-symbol evidence cards showing pass/fail status and test links.

---

## 9. Historical Notes & Retained Decisions

- `architecture-revised.md` is retained in the repository root for historical reference regarding initial planning and decision evolution. `.agent/architecture.md` remains the authoritative live reference.
- Tree-sitter, multi-language support, graph databases (Neo4j), dynamic test generation, and TypeScript were explicitly evaluated and rejected for MVP complexity control (see ADR-001 through ADR-011 in `decisions.md`).
