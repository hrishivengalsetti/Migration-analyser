# Technical Architecture

## Repository Structure

```
hackathon/
├── .agent/                  ← Project memory (this directory)
├── backend/                 ← Python + FastAPI
│   ├── main.py
│   ├── models.py            ← Pydantic models + SQLite schema
│   ├── database.py          ← SQLite connection + queries
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── runner.py        ← Pipeline orchestrator (BackgroundTask)
│   │   ├── diff_analyzer.py ← File + AST symbol diff
│   │   ├── graph_builder.py ← NetworkX graph from ast
│   │   ├── blast_radius.py  ← Graph reachability
│   │   ├── test_selector.py ← Symbol-to-test mapping
│   │   ├── sandbox.py       ← Docker SDK execution
│   │   ├── comparator.py    ← Deterministic result comparison
│   │   ├── evidence.py      ← Evidence assembly
│   │   ├── interpreter.py   ← Gemini Flash LLM call
│   │   └── report.py        ← Report assembly + classification
│   ├── requirements.txt
│   └── tests/
│       ├── test_diff_analyzer.py
│       ├── test_graph_builder.py
│       ├── test_blast_radius.py
│       ├── test_test_selector.py
│       ├── test_sandbox.py
│       ├── test_comparator.py
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
└── README.md
```

---

## Backend: Python + FastAPI

### API Endpoints

```
POST /api/runs
  Body: multipart/form-data { original: <zip>, migrated: <zip> }
  Response: { run_id: UUID, status: "pending" }

GET /api/runs/{run_id}
  Response: { run_id, status, created_at, error? }

GET /api/runs/{run_id}/report
  Response: Report (full structured JSON)
```

### Pipeline Execution

- `POST /api/runs` creates a Run record in SQLite and fires a `BackgroundTask`
- The BackgroundTask runs the full pipeline sequentially
- Status is updated at each step in SQLite
- Frontend polls `GET /api/runs/{run_id}` until status == "complete" or "failed"

### Pipeline Steps (in order)

1. **DiffAnalyzer** → `[FileDiff]`, `[SymbolDiff]`
2. **GraphBuilder** → `CodeGraph` (original), `CodeGraph` (migrated)
3. **BlastRadius** → `BlastRadius`
4. **TestSelector** → `{symbol_id: [test_id]}`
5. **SandboxExecutor** → `[TestResult]` × 2
6. **Comparator** → `{test_id: comparison}`
7. **EvidenceCollector** → `[Evidence]`
8. **Interpreter** → `AIInterpretation` (1 Gemini Flash call)
9. **ReportAssembler** → `Report` (classification is deterministic)

---

## Database: SQLite

### Schema

```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    original_path TEXT,
    migrated_path TEXT,
    error TEXT
);

CREATE TABLE reports (
    run_id TEXT PRIMARY KEY,
    data TEXT NOT NULL,   -- JSON blob of the full Report
    generated_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
```

The report is stored as a JSON blob. No complex relational schema needed for MVP.
The code graph is stored as a JSON file on disk: `runs/{run_id}/graph_original.json`, `runs/{run_id}/graph_migrated.json`.

---

## Graph: NetworkX

### Node Types

```python
# Node attributes
{
    "id": "mymodule.MyClass.my_method",
    "kind": "function",      # or "class", "module"
    "file": "mymodule/utils.py",
    "line_start": 42,
    "line_end": 58,
    "version": "original"   # or "migrated"
}
```

### Edge Types

```python
# Edge attributes
{
    "kind": "calls",    # or "imports"
    "line": 45
}
```

### Blast Radius Algorithm

```python
import networkx as nx

def compute_blast_radius(graph: nx.DiGraph, changed_symbols: list[str]) -> BlastRadius:
    """
    For each changed symbol, find all symbols that could be affected.
    'Affected' = nodes that have a path TO the changed symbol (callers).
    Uses NetworkX ancestors() which finds all nodes with a path to the given node.
    """
    directly_affected = set()
    transitively_affected = set()

    for sym in changed_symbols:
        if sym not in graph:
            continue
        # Who calls this changed symbol? (ancestors in call graph)
        ancestors = nx.ancestors(graph, sym)
        for a in ancestors:
            # 1-hop neighbors
            if sym in graph.successors(a) or a in graph.successors(sym):
                directly_affected.add(a)
            else:
                transitively_affected.add(a)

    cycles = not nx.is_directed_acyclic_graph(graph)
    return BlastRadius(
        changed_symbols=changed_symbols,
        directly_affected=list(directly_affected),
        transitively_affected=list(transitively_affected),
        cycles_detected=cycles
    )
```

---

## Sandbox: Docker

### Image

```dockerfile
# docker/test-runner/Dockerfile
FROM python:3.11-slim
RUN pip install --no-cache-dir pytest pytest-json-report
WORKDIR /workspace
USER nobody
```

### Execution

```python
import docker

client = docker.from_env()

result = client.containers.run(
    image="migration-verifier-runner:latest",
    command=["pytest", "/workspace", "--json-report", "--json-report-file=/tmp/results.json", "-q"],
    volumes={str(code_path): {"bind": "/workspace", "mode": "ro"}},
    network_disabled=True,
    mem_limit="512m",
    nano_cpus=1_000_000_000,  # 1 CPU
    pids_limit=100,
    remove=True,
    stdout=True,
    stderr=True,
)
```

---

## AI: Gemini Flash

### When

Once per run, after all evidence is collected.

### What It Receives

```json
{
  "changed_files": [...],
  "changed_symbols": [...],
  "blast_radius_size": 14,
  "evidence": [
    {
      "symbol_id": "api.client.fetch_data",
      "comparison": "regression",
      "failing_tests": ["test_api.test_fetch_data_encoding"]
    }
  ],
  "regressions": 2,
  "classification": "regression_detected"
}
```

### What It Returns

```json
{
  "migration_intent": "...",
  "risk_summary": "...",
  "key_concerns": ["...", "..."],
  "confidence": "high"
}
```

### Prompt Location

`backend/pipeline/prompts/interpreter.txt` — version controlled, not embedded in code.

---

## Frontend: React + Vite + JS + Tailwind + shadcn

### Pages

1. **Upload Page** (`/`) — Two zip file inputs + "Analyze" button + status polling
2. **Report Page** (`/report/:runId`) — Tabbed report viewer

### Report Tabs

1. **Summary** — Classification badge, counts, AI narrative
2. **Changes** — File diff + symbol diff viewer
3. **Impact** — React Flow graph of blast radius
4. **Tests** — Test results table (original vs migrated comparison)
5. **Evidence** — Per-symbol evidence cards

---

## Classification Logic (Deterministic)

```python
def classify(evidence: list[Evidence], tests_run: int) -> Classification:
    regressions = sum(1 for e in evidence if e.comparison == "regression")
    no_tests = sum(1 for e in evidence if e.comparison == "no_tests")

    if regressions > 0:
        return "regression_detected"
    elif tests_run == 0 or no_tests == len(evidence):
        return "unverified"
    elif no_tests > 0:
        return "partially_verified"
    else:
        return "verified"
```

AI does **not** influence this classification. AI only narrates it.

---

## Key Technology Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| Parsing | Python `ast` stdlib | Python-only MVP; no FFI overhead |
| Graph engine | NetworkX | Sufficient for demo scale; no graph DB needed |
| Graph persistence | JSON file per run | Simple, inspectable |
| Run state | SQLite | Single-user; no hosted DB needed |
| Sandbox | Docker (pre-built image) | Required; Option A for simplicity |
| LLM | Google Gemini Flash | Free tier, hackathon-friendly |
| Frontend | React + Vite + JS + Tailwind + shadcn | Justified by report complexity |
| Graph viz | React Flow | Pre-built, visually impressive |
| Code submission | Zip upload | Better UX for potential remote demo |
| Demo migration | Purpose-built project | Full control; demo always works |
| TypeScript | Dropped for MVP | Reduces friction; JS is sufficient |
| Tree-sitter | Dropped for MVP | Overkill; `ast` handles Python |
| Test generation | Dropped from MVP | Unreliable; doesn't add demo credibility |
