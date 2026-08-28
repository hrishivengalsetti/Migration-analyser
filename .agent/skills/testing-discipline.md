# SKILL: Testing Discipline

## Purpose

Prevent test suite inflation, endless fix/fail loops, and ensure meaningful test coverage for the MVP.

---

## The Testing Philosophy

> Write tests that verify the task's acceptance criteria. No more. No less.

---

## What to Test

For each task, the task file specifies a `pytest` command. Write tests that make that command pass.

Tests should verify:
- The happy path (the normal demo flow)
- The explicit edge cases mentioned in the acceptance criteria
- The error handling specified in the task

Tests should NOT verify:
- Every possible edge case
- Internal implementation details
- Behavior that will be changed in a later task
- Things that are explicitly out of scope in the task

---

## Test File Location

All backend tests go in `backend/tests/`.

Naming convention: `test_<module>.py` for the module being tested.

Example:
```
backend/pipeline/diff_analyzer.py  →  backend/tests/test_diff_analyzer.py
```

---

## Test Structure

```python
# test_diff_analyzer.py

import pytest
from pipeline.diff_analyzer import analyze_file_diff, analyze_symbol_diff

class TestFileDiff:
    def test_detects_modified_file(self, tmp_path):
        # Arrange
        ...
        # Act
        result = analyze_file_diff(original_dir, migrated_dir)
        # Assert
        assert len(result) == 1
        assert result[0].status == "modified"

    def test_detects_added_file(self, tmp_path):
        ...
```

---

## Debug Loop Limits

When a test fails:

**Attempt 1**: Read the error. Make the minimal fix. Re-run.

**Attempt 2**: Read the error again. Make a different minimal fix. Re-run.

**After 2 attempts**: STOP. Report the blocker. Do not continue.

The debug loop limit is **2 attempts**. This is a hard constraint, not a guideline.

---

## What "Pass" Means

A test passes when:
- The `pytest` exit code is 0
- No tests are unexpectedly skipped
- No warnings-as-errors are triggered (unless the task requires this)

---

## Mocking External Dependencies

- Mock the Docker daemon in sandbox tests
- Mock the Gemini API in interpreter tests
- Use real filesystem operations (tmp_path) for file-based tests
- Do NOT mock `ast`, `networkx`, or `difflib`

---

## Do NOT Do These

- Add tests for modules not mentioned in the current task
- Add tests to "improve coverage" beyond what the task specifies
- Write tests that require a running Docker daemon when the task says to mock it
- Write tests that make real LLM API calls
- Modify existing passing tests to make failing ones pass
- Skip a failing test to make the suite green (`@pytest.mark.skip`)
