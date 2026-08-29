# TASK-007: Test Selector — Static Symbol-to-Test Mapping

**Milestone**: M4  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-006 (complete)  

---

## Goal

Implement the test selector that maps existing pytest test functions to changed and blast-radius-affected symbols using static AST analysis. Given a codebase directory, the list of affected symbols (from `BlastRadius.all_affected` + `BlastRadius.changed_symbols`), parse all test files and determine which test functions exercise which target symbols via imports and calls. Return the subset of test functions that are relevant to the migration changes.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/pipeline/blast_radius.py` (from TASK-006)
4. `backend/models.py`
5. This task file

---

## Inputs

- `codebase_dir: Path` — path to the migrated codebase directory (unzipped)
- `affected_symbols: list[str]` — union of `BlastRadius.changed_symbols` + `BlastRadius.all_affected`

## Outputs

```
backend/pipeline/test_selector.py    ← New file
backend/tests/test_test_selector.py  ← New file
```

---

## Acceptance Criteria

### AC-1: Discovers test files
- Finds all files matching `test_*.py` or `*_test.py` patterns recursively in `codebase_dir`
- Ignores `__pycache__/` and hidden directories

### AC-2: Extracts test functions
- Identifies all top-level functions whose name starts with `test_` in test files
- Identifies all methods whose name starts with `test_` inside classes (test classes)
- Each test function is identified by its symbol_id using the same format as TASK-004 (e.g., `tests.test_pricing.test_discount_applies`)

### AC-3: Maps tests to target symbols
- For each test function, performs AST analysis to discover which project symbols the test references:
  1. Parse `import` and `from ... import ...` statements in the test file
  2. Parse `ast.Call` nodes inside the test function body to find called names
  3. Resolve called names against the file's import context to produce full symbol IDs
  4. If a resolved symbol ID is in `affected_symbols`, the test is considered "affected"
- Resolution is best-effort static analysis. Unresolvable names are silently ignored.

### AC-4: Returns affected test list
- Returns only the test functions that reference at least one symbol in `affected_symbols`
- Returns empty list if no tests cover any affected symbol

### AC-5: Function signature
```python
def select_tests(
    codebase_dir: Path,
    affected_symbols: list[str]
) -> list[str]:
    """
    Returns list of test function symbol_ids that cover affected symbols.
    Example return: ["tests.test_pricing.test_discount_applies", "tests.test_checkout.test_total"]
    """
    ...
```

### AC-6: All tests pass
- `cd backend && pytest tests/test_test_selector.py -v` exits with code 0

---

## Non-Goals

- Do NOT execute any tests (that is TASK-008B)
- Do NOT resolve dynamic calls, `getattr()`, or `importlib` usage
- Do NOT analyze pytest fixtures or conftest.py for transitive dependencies
- Do NOT analyze parameterized test markers
- Do NOT filter by test class names — only by function/method names starting with `test_`
- Do NOT modify or integrate into `runner.py` yet (that is TASK-012)

---

## Technical Constraints

- Use Python `ast` stdlib only for parsing
- Do NOT use `pytest --collect-only` or subprocess calls
- Do NOT add new dependencies
- Use the same import resolution approach as TASK-005 (graph builder): resolve `from X import Y` to full symbol IDs based on known project symbols

---

## Algorithm

```python
import ast
from pathlib import Path

def select_tests(codebase_dir: Path, affected_symbols: list[str]) -> list[str]:
    affected_set = set(affected_symbols)
    selected_tests = []

    # Find all test files
    test_files = [
        p for p in codebase_dir.rglob("*.py")
        if (p.name.startswith("test_") or p.name.endswith("_test.py"))
        and not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    ]

    for test_file in test_files:
        source = test_file.read_text(errors='replace')
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        # Determine module name from relative path
        rel_path = test_file.relative_to(codebase_dir)
        module_name = str(rel_path.with_suffix('')).replace('/', '.').replace('\\', '.')

        # Build import map: local_name -> full_symbol_id
        import_map = _build_import_map(tree)

        # Extract test functions (top-level and class methods)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    test_id = f"{module_name}.{node.name}"
                    if _test_references_affected(node, import_map, affected_set):
                        selected_tests.append(test_id)
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name.startswith("test_"):
                            test_id = f"{module_name}.{node.name}.{item.name}"
                            if _test_references_affected(item, import_map, affected_set):
                                selected_tests.append(test_id)

    return sorted(selected_tests)


def _build_import_map(tree: ast.Module) -> dict[str, str]:
    """Map local imported names to their full module/symbol paths."""
    import_map = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split('.')[-1]
                import_map[local_name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    import_map[local_name] = f"{node.module}.{alias.name}"
    return import_map


def _test_references_affected(
    func_node: ast.FunctionDef,
    import_map: dict[str, str],
    affected_set: set[str]
) -> bool:
    """Check if a test function body references any affected symbol."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            called_name = _extract_call_name(node)
            if called_name and called_name in import_map:
                resolved = import_map[called_name]
                if resolved in affected_set:
                    return True
        # Also check for attribute access patterns: obj.method()
        if isinstance(node, ast.Attribute):
            # Check if the attribute name matches any affected symbol suffix
            pass  # Keep simple — only resolve direct imports
    return False


def _extract_call_name(call_node: ast.Call) -> str | None:
    """Extract the called function name from a Call node."""
    if isinstance(call_node.func, ast.Name):
        return call_node.func.id
    elif isinstance(call_node.func, ast.Attribute):
        # e.g., module.func() — return the attribute name
        return call_node.func.attr
    return None
```

You may implement this exactly as shown or adjust as long as all ACs pass.

---

## Test Requirements

Write tests in `backend/tests/test_test_selector.py` using `tmp_path`:

Create a small project structure with `tmp_path`:
- A source module `mypackage/pricing.py` with function `calculate_discount()`
- A test file `tests/test_pricing.py` that imports and calls `calculate_discount()`
- A test file `tests/test_other.py` that does NOT reference any affected symbol

1. `test_selects_test_covering_affected_symbol` — test that imports+calls an affected symbol → selected
2. `test_excludes_test_not_covering_affected_symbol` — test with no reference to affected symbols → not selected
3. `test_returns_empty_when_no_tests_exist` — no test files → empty list
4. `test_returns_empty_when_no_affected_symbols` — empty affected_symbols list → empty result
5. `test_handles_syntax_error_in_test_file` — test file with syntax error → skipped, no crash
6. `test_discovers_test_methods_in_class` — test method inside a class → selected if it covers affected symbol
7. `test_symbol_id_format_correct` — returned test IDs follow `module.function` format

---

## Verification

```bash
cd backend && pytest tests/test_test_selector.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
