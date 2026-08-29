# TASK-009: Result Comparator — Deterministic Behavioral Comparison

**Milestone**: M6  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-008B (complete)  

---

## Goal

Implement the deterministic result comparator that takes test execution outputs from both the original and migrated codebase runs (from TASK-008B) and compares them per test function. Categorize each test into one of four comparison outcomes: PASSED_BOTH, REGRESSION, IMPROVEMENT, or FAILED_BOTH. This is purely deterministic — no AI involved.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/pipeline/sandbox.py` (from TASK-008B)
4. `backend/models.py`
5. This task file

---

## Inputs

- `original_results: dict` — test results from running pytest on the original codebase (output of `run_tests_in_sandbox`)
- `migrated_results: dict` — test results from running pytest on the migrated codebase (output of `run_tests_in_sandbox`)

## Outputs

```
backend/pipeline/comparator.py      ← New file
backend/tests/test_comparator.py    ← New file
```

---

## Data Structures

The comparator works with the sandbox output dict format from TASK-008B:

```python
# Input format (from sandbox.py):
{
    "tests": [
        {"nodeid": "test_module.py::test_func", "outcome": "passed"|"failed"|"error", ...},
        ...
    ],
    ...
}

# Output format:
class TestComparison:
    """Not a Pydantic model — just a plain dict for pipeline data flow."""
    # {
    #     "test_id": "test_module.py::test_func",
    #     "original_outcome": "passed" | "failed" | "error" | "skipped" | "missing",
    #     "migrated_outcome": "passed" | "failed" | "error" | "skipped" | "missing",
    #     "comparison": "passed_both" | "regression" | "improvement" | "failed_both"
    # }
```

---

## Acceptance Criteria

### AC-1: Function signature
```python
def compare_results(
    original_results: dict,
    migrated_results: dict
) -> list[dict]:
    """
    Returns list of per-test comparison dicts.
    Each dict has keys: test_id, original_outcome, migrated_outcome, comparison
    """
    ...
```

### AC-2: Comparison categories
- `"passed_both"`: `original=passed` AND `migrated=passed`
- `"regression"`: `original=passed` AND `migrated` is `failed` or `error`
- `"improvement"`: `original` is `failed` or `error` AND `migrated=passed`
- `"failed_both"`: `original` is `failed` or `error` AND `migrated` is `failed` or `error`

### AC-3: Handles missing tests
- If a test exists in original but not in migrated: `migrated_outcome="missing"`, `comparison="regression"`
- If a test exists in migrated but not in original: `original_outcome="missing"`, `comparison="improvement"`
- Do NOT crash on mismatched test sets

### AC-4: Handles skipped tests
- If a test is `"skipped"` in either run, treat it as not providing evidence:
  - `skipped` + `passed` → `"improvement"` (conservative)
  - `skipped` + `failed` → `"failed_both"` (conservative)
  - `skipped` + `skipped` → `"passed_both"` (no signal either way)

### AC-5: Test ID matching
- Match tests by their `nodeid` field (e.g., `test_pricing.py::test_discount_applies`)
- Build a union of all test IDs from both runs

### AC-6: Deterministic output
- Results are sorted alphabetically by `test_id`
- Same inputs always produce same output

### AC-7: All tests pass
- `cd backend && pytest tests/test_comparator.py -v` exits with code 0

---

## Non-Goals

- Do NOT execute any tests (that was TASK-008B)
- Do NOT use AI for comparison
- Do NOT compute code diffs — only compare test outcomes
- Do NOT integrate into `runner.py` yet (that is TASK-012)
- Do NOT compare stdout/stderr content — only pass/fail status

---

## Technical Constraints

- Pure Python, no external dependencies
- No subprocess calls
- Deterministic — no randomness

---

## Algorithm

```python
def compare_results(original_results: dict, migrated_results: dict) -> list[dict]:
    # Build lookup: nodeid -> outcome
    orig_map = {t["nodeid"]: t["outcome"] for t in original_results.get("tests", [])}
    migr_map = {t["nodeid"]: t["outcome"] for t in migrated_results.get("tests", [])}

    all_test_ids = sorted(set(orig_map.keys()) | set(migr_map.keys()))

    comparisons = []
    for test_id in all_test_ids:
        orig = orig_map.get(test_id, "missing")
        migr = migr_map.get(test_id, "missing")

        comparison = _classify_comparison(orig, migr)
        comparisons.append({
            "test_id": test_id,
            "original_outcome": orig,
            "migrated_outcome": migr,
            "comparison": comparison,
        })

    return comparisons


def _classify_comparison(orig: str, migr: str) -> str:
    orig_pass = orig in ("passed", "skipped")
    migr_pass = migr in ("passed", "skipped")
    orig_fail = orig in ("failed", "error", "missing")
    migr_fail = migr in ("failed", "error", "missing")

    if orig == "passed" and migr == "passed":
        return "passed_both"
    elif orig == "skipped" and migr == "skipped":
        return "passed_both"
    elif orig_pass and migr_fail:
        return "regression"
    elif orig_fail and migr_pass:
        return "improvement"
    elif orig_fail and migr_fail:
        return "failed_both"
    else:
        return "passed_both"  # fallback for edge cases like skipped+passed
```

You may implement this exactly as shown or adjust as long as all ACs pass.

---

## Test Requirements

Write tests in `backend/tests/test_comparator.py`:

1. `test_passed_both` — both pass → `"passed_both"`
2. `test_regression_detected` — original passes, migrated fails → `"regression"`
3. `test_improvement_detected` — original fails, migrated passes → `"improvement"`
4. `test_failed_both` — both fail → `"failed_both"`
5. `test_missing_in_migrated` — test only in original → `"regression"` with `migrated_outcome="missing"`
6. `test_missing_in_original` — test only in migrated → `"improvement"` with `original_outcome="missing"`
7. `test_deterministic_ordering` — results sorted by test_id
8. `test_empty_results` — both empty → empty list
9. `test_handles_error_outcome` — `"error"` treated same as `"failed"`

---

## Verification

```bash
cd backend && pytest tests/test_comparator.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
