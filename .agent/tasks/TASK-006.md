# TASK-006: Blast Radius Engine

**Milestone**: M3  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-005 (complete)  

---

## Goal

Implement the blast radius calculator. Given a code graph (from TASK-005) and a list of changed symbol IDs (from TASK-004), compute which other symbols in the codebase could be affected by the changes. Uses NetworkX graph reachability.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/pipeline/graph_builder.py` (from TASK-005)
4. `backend/models.py`
5. This task file

---

## Inputs

- `graph: nx.DiGraph` — the code graph from TASK-005
- `changed_symbols: list[str]` — symbol IDs of changed symbols from TASK-004

## Outputs

```
backend/pipeline/blast_radius.py    ← New file
backend/models.py                   ← Updated: add BlastRadius model
backend/tests/test_blast_radius.py  ← New file
```

---

## Data Models (add to models.py)

```python
class BlastRadius(BaseModel):
    changed_symbols: list[str]
    directly_affected: list[str]      # 1-hop ancestors of changed symbols
    transitively_affected: list[str]  # all other ancestors
    all_affected: list[str]           # union of directly + transitively
    cycles_detected: bool
    total_affected_count: int
```

---

## Acceptance Criteria

### AC-1: Direct dependencies detected
- A symbol that directly calls or imports a changed symbol is in `directly_affected`

### AC-2: Transitive dependencies detected
- A symbol that calls something that calls a changed symbol is in `transitively_affected`

### AC-3: Cycles handled
- If the graph has cycles, `cycles_detected=True`
- Cycle detection does NOT crash the analysis — it uses `nx.ancestors()` which handles cycles correctly
- Just set the flag and continue

### AC-4: Changed symbols excluded from affected
- The changed symbols themselves are NOT in `directly_affected` or `transitively_affected`

### AC-5: Symbols not in graph ignored
- If a changed symbol ID does not exist in the graph, it is skipped silently

### AC-6: Deterministic ordering
- All lists are sorted alphabetically
- Running the same analysis twice produces the same result

### AC-7: all_affected is correct union
- `all_affected` = `directly_affected` ∪ `transitively_affected` (no duplicates, sorted)

### AC-8: Function signature
```python
def compute_blast_radius(
    graph: nx.DiGraph,
    changed_symbols: list[str]
) -> BlastRadius:
    ...
```

### AC-9: All tests pass

---

## Non-Goals

- Do NOT compute "who does the changed symbol affect downstream" — compute "who calls the changed symbol" (upstream callers)
- Do NOT modify the graph
- Do NOT rank or prioritize affected symbols (that is the evidence + AI layer)

---

## Technical Constraints

- `networkx.ancestors(G, node)` returns all nodes with a directed path TO `node`
- This is the correct function for "who calls this symbol"
- Do NOT implement your own reachability algorithm

---

## Algorithm

```python
import networkx as nx
from models import BlastRadius

def compute_blast_radius(graph: nx.DiGraph, changed_symbols: list[str]) -> BlastRadius:
    changed_set = set(changed_symbols)
    all_ancestors = set()

    for sym in changed_symbols:
        if sym not in graph:
            continue
        try:
            ancestors = nx.ancestors(graph, sym)
        except nx.NetworkXError:
            continue
        all_ancestors.update(ancestors)

    # Remove changed symbols themselves from the affected set
    all_ancestors -= changed_set

    # Classify as directly affected (1-hop) vs transitively affected
    directly_affected = set()
    for sym in changed_symbols:
        if sym not in graph:
            continue
        # Direct predecessors (nodes with an edge directly to sym)
        for predecessor in graph.predecessors(sym):
            if predecessor not in changed_set:
                directly_affected.add(predecessor)

    transitively_affected = all_ancestors - directly_affected

    cycles_detected = not nx.is_directed_acyclic_graph(graph)

    all_affected = sorted(directly_affected | transitively_affected)

    return BlastRadius(
        changed_symbols=sorted(changed_symbols),
        directly_affected=sorted(directly_affected),
        transitively_affected=sorted(transitively_affected),
        all_affected=all_affected,
        cycles_detected=cycles_detected,
        total_affected_count=len(all_affected),
    )
```

You may implement this exactly as shown or adjust as long as all ACs pass.

---

## Test Requirements

Write tests in `backend/tests/test_blast_radius.py`:

Build small test graphs using NetworkX directly (do not use real Python files).

1. `test_direct_caller_detected` — A→B, B changes → A is directly affected
2. `test_transitive_caller_detected` — A→B→C, C changes → B directly affected, A transitively affected
3. `test_changed_symbol_excluded_from_affected` — changed symbol not in directly_affected or transitively_affected
4. `test_symbol_not_in_graph_ignored` — gracefully handles unknown symbol
5. `test_cycle_detected` — A→B→A → cycles_detected=True, no crash
6. `test_deterministic_ordering` — same result on second call
7. `test_all_affected_is_union` — all_affected = directly ∪ transitively

---

## Verification

```bash
cd backend && pytest tests/test_blast_radius.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
