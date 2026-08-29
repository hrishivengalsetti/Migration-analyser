# TASK-010A: Evidence Collector & Classification Engine

**Milestone**: M6  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-009 (complete), TASK-007 (complete)  

---

## Goal

Implement the evidence collector that assembles per-symbol evidence cards by combining symbol diffs, test selection mappings, and test comparison results. Also implement the deterministic classification algorithm that computes the overall migration verdict (VERIFIED, PARTIALLY_VERIFIED, REGRESSION_DETECTED, UNVERIFIED). The classification is strictly deterministic and MUST match the logic in `.agent/architecture.md` exactly. AI never overrides classification.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md` (especially Section 4: Classification Logic)
3. `backend/pipeline/comparator.py` (from TASK-009)
4. `backend/pipeline/test_selector.py` (from TASK-007)
5. This task file

---

## Inputs

- `symbol_diffs: list[SymbolDiff]` — from TASK-004
- `blast_radius: BlastRadius` — from TASK-006
- `selected_tests: list[str]` — test symbol IDs from TASK-007
- `comparisons: list[dict]` — per-test comparison results from TASK-009

## Outputs

```
backend/pipeline/evidence.py         ← New file
backend/tests/test_evidence.py       ← New file
```

---

## Data Models (use from models.py — already defined)

```python
# These should already exist in models.py from TASK-001:
class Evidence(BaseModel):
    symbol_id: str
    file: str
    change_kind: Optional[SymbolChangeKind] = None
    comparison: str  # "verified", "regression", "improved", "no_tests"
    failing_tests: list[str] = []
    passing_tests: list[str] = []

class Classification(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    REGRESSION_DETECTED = "regression_detected"
    UNVERIFIED = "unverified"
```

---

## Acceptance Criteria

### AC-1: Evidence collection function signature
```python
def collect_evidence(
    symbol_diffs: list[SymbolDiff],
    blast_radius: BlastRadius,
    selected_tests: list[str],
    comparisons: list[dict],
    test_to_symbols: dict[str, list[str]]
) -> list[Evidence]:
    """
    test_to_symbols: mapping from test function ID to list of symbol IDs it covers.
    Produced by test_selector as a secondary output.
    """
    ...
```

### AC-2: Per-symbol evidence assembly
- For each symbol in `symbol_diffs` (the changed symbols):
  - Find all tests that cover this symbol (via `test_to_symbols` reverse lookup)
  - Check comparisons for those tests
  - Determine per-symbol comparison status:
    - `"regression"`: at least one covering test has `comparison="regression"`
    - `"verified"`: all covering tests have `comparison="passed_both"` and at least one test covers the symbol
    - `"improved"`: at least one test has `comparison="improvement"` and none have `comparison="regression"`
    - `"no_tests"`: no tests cover this symbol
  - Populate `failing_tests` with test IDs that regressed
  - Populate `passing_tests` with test IDs that passed both

### AC-3: Classification function signature
```python
def classify(evidence: list[Evidence], tests_run: int) -> Classification:
    ...
```

### AC-4: Classification logic — EXACT match to architecture
The classification MUST implement this exact logic from `.agent/architecture.md`:
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
**This logic is non-negotiable. Do not modify it.**

### AC-5: Edge case — empty evidence
- If `symbol_diffs` is empty (no changes detected), return empty evidence list
- If evidence is empty and tests_run is 0, classification is `UNVERIFIED`

### AC-6: All tests pass
- `cd backend && pytest tests/test_evidence.py -v` exits with code 0

---

## Non-Goals

- Do NOT use AI for classification — this is strictly deterministic
- Do NOT generate new tests
- Do NOT modify any upstream pipeline outputs
- Do NOT integrate into `runner.py` yet (that is TASK-012)
- Do NOT implement report assembly (that is TASK-010B)

---

## Technical Constraints

- Pure Python, no external dependencies
- Classification logic must be a verbatim implementation of the architecture spec
- Evidence cards must be serializable Pydantic models

---

## Test Requirements

Write tests in `backend/tests/test_evidence.py`:

1. `test_evidence_regression_when_test_fails` — symbol with a covering test that regressed → `comparison="regression"`, symbol in `failing_tests`
2. `test_evidence_verified_when_all_tests_pass` — symbol with all covering tests passing → `comparison="verified"`, tests in `passing_tests`
3. `test_evidence_no_tests_when_uncovered` — symbol with no covering tests → `comparison="no_tests"`
4. `test_evidence_improved_when_test_improves` — symbol with improving test → `comparison="improved"`
5. `test_classify_regression_detected` — any regression → `Classification.REGRESSION_DETECTED`
6. `test_classify_verified` — all verified, zero regressions → `Classification.VERIFIED`
7. `test_classify_partially_verified` — mix of verified and no_tests → `Classification.PARTIALLY_VERIFIED`
8. `test_classify_unverified_no_tests_run` — tests_run=0 → `Classification.UNVERIFIED`
9. `test_classify_unverified_all_no_tests` — all evidence has `no_tests` → `Classification.UNVERIFIED`
10. `test_classify_empty_evidence` — empty evidence, tests_run=0 → `Classification.UNVERIFIED`

---

## Verification

```bash
cd backend && pytest tests/test_evidence.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
