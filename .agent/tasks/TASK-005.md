# TASK-005: Code Graph Builder

**Milestone**: M3  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-004 (complete)  

---

## Goal

Build a NetworkX directed graph representing the import and call relationships in a Python codebase. Each node is a symbol (function, class, method, or module). Each edge represents either an import or a call relationship. The graph is serialized to JSON. This enables blast radius analysis in TASK-006.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/pipeline/diff_analyzer.py`
4. `backend/models.py`
5. This task file

---

## Inputs

- `codebase_dir: Path` — directory of a Python codebase

## Outputs

```
backend/pipeline/graph_builder.py   ← New file
backend/models.py                   ← Updated: add CodeGraph model
backend/tests/test_graph_builder.py ← New file
```

---

## Data Models (add to models.py)

```python
class CodeGraph(BaseModel):
    run_id: str
    version: Literal["original", "migrated"]
    nodes: list[dict]   # networkx node_link_data format
    edges: list[dict]   # networkx node_link_data format
    # Stored as JSON file: data/runs/{run_id}/graph_{version}.json

    @classmethod
    def from_networkx(cls, G: nx.DiGraph, run_id: str, version: str) -> "CodeGraph":
        data = nx.node_link_data(G)
        return cls(run_id=run_id, version=version, nodes=data["nodes"], edges=data["links"])

    def to_networkx(self) -> nx.DiGraph:
        data = {"nodes": self.nodes, "links": self.edges, "directed": True, "multigraph": False, "graph": {}}
        return nx.node_link_graph(data)
```

---

## Acceptance Criteria

### AC-1: Build graph from codebase
- Walks all `.py` files in `codebase_dir`
- Ignores `__pycache__/` and hidden directories
- Returns a `networkx.DiGraph`

### AC-2: Nodes represent symbols
- Each node has attributes: `id` (string), `kind` ("function"/"class"/"method"/"module"), `file` (relative path), `line_start` (int)
- Node ID format is the same as TASK-004 symbol IDs: `module.ClassName.method_name`

### AC-3: Import edges
- `import mypackage.utils` in `mypackage/api.py` → edge from `mypackage.api` to `mypackage.utils`
- `from mypackage.utils import helper_func` → edge from `mypackage.api` to `mypackage.utils.helper_func`
- Edge has attribute: `kind="imports"`

### AC-4: Call edges (best-effort static analysis)
- `helper_func()` called inside `my_function` → edge from `mypackage.api.my_function` to `mypackage.utils.helper_func`
- Only add call edges for names that can be resolved to a known symbol in the graph
- Unresolvable names are silently ignored (do not raise errors)
- Edge has attribute: `kind="calls"`

### AC-5: Serialization
```python
def save_graph(G: nx.DiGraph, path: Path) -> None:
    data = nx.node_link_data(G)
    path.write_text(json.dumps(data, indent=2))

def load_graph(path: Path) -> nx.DiGraph:
    data = json.loads(path.read_text())
    return nx.node_link_graph(data)
```

### AC-6: Function signature
```python
def build_graph(codebase_dir: Path) -> nx.DiGraph:
    ...
```

### AC-7: All tests pass

---

## Non-Goals

- Do NOT resolve cross-package (third-party) imports — only intra-project symbols
- Do NOT handle dynamic attribute access or `getattr()` calls
- Do NOT handle `__import__()` or `importlib`
- Do NOT analyze runtime behavior — this is STATIC analysis only
- Do NOT handle decorators as call edges
- Accuracy is "best effort" — the graph will miss some relationships. Document this.

---

## Technical Constraints

- `networkx` library (add to `requirements.txt`)
- Python `ast` stdlib for parsing
- `json` stdlib for serialization

---

## Algorithm Notes

### Two-pass approach

**Pass 1**: Extract all symbols from all files. Build the node set.
**Pass 2**: Walk all files again. For each file:
- Extract imports → add import edges to known symbols
- Extract function calls → add call edges to known symbols

### Resolving imports

```python
# from mypackage.utils import helper_func
# → check if "mypackage.utils.helper_func" is in graph nodes
# → if yes, add edge (current_module, "mypackage.utils.helper_func", kind="imports")

# import mypackage.utils
# → check if "mypackage.utils" is in graph nodes (module-level node)
# → if yes, add edge (current_module, "mypackage.utils", kind="imports")
```

### Resolving calls

```python
# Inside mypackage.api.fetch_data():
#   helper_func()
# → look up "helper_func" in the import context of this file
# → resolve to full symbol ID if found
# → add edge (mypackage.api.fetch_data, resolved_id, kind="calls")
```

Call resolution is inherently imperfect. Resolve only names imported in the current file's scope. Ignore the rest.

---

## Test Requirements

Write tests in `backend/tests/test_graph_builder.py` using `tmp_path`:

1. `test_builds_nodes_for_functions` — functions become nodes
2. `test_builds_nodes_for_classes` — classes become nodes
3. `test_import_edge_from_import_statement` — `import x.y` → import edge
4. `test_import_edge_from_from_import` — `from x.y import z` → import edge to specific symbol
5. `test_call_edge_for_known_function` — calling an imported function → call edge
6. `test_ignores_unknown_calls` — calling a name not in graph → no error, no edge
7. `test_graph_serialization_roundtrip` — save and load produces equivalent graph
8. `test_ignores_pycache` — no nodes from `__pycache__/`

---

## Verification

```bash
cd backend && pytest tests/test_graph_builder.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
