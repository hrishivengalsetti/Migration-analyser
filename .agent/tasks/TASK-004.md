# TASK-004: Diff Analyzer — AST Symbol Diff

**Milestone**: M2  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-003 (complete)  

---

## Goal

Implement the AST-level symbol diff. For each modified Python file (from TASK-003), extract the function and class definitions from both versions and determine which symbols were added, deleted, or modified (body or signature changed). This is the foundation for blast radius analysis.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/pipeline/diff_analyzer.py` (from TASK-003)
4. `backend/models.py`
5. This task file

---

## Inputs

- `file_diffs: list[FileDiff]` — from TASK-003
- Original and migrated directories

## Outputs

```
backend/pipeline/diff_analyzer.py   ← Updated: add analyze_symbol_diff()
backend/models.py                   ← Updated: add SymbolDiff, SymbolKind, SymbolChangeKind
backend/tests/test_diff_analyzer.py ← Updated: add symbol diff tests
```

---

## Data Models (add to models.py)

```python
class SymbolKind(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"

class SymbolChangeKind(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    BODY_CHANGED = "body_changed"
    SIGNATURE_CHANGED = "signature_changed"

class SymbolDiff(BaseModel):
    symbol_id: str              # e.g. "mymodule.MyClass.my_method"
    file: str                   # relative path
    kind: SymbolKind
    change_kind: SymbolChangeKind
    original_source: Optional[str] = None
    migrated_source: Optional[str] = None
    line_original: Optional[int] = None
    line_migrated: Optional[int] = None
```

---

## Acceptance Criteria

### AC-1: Extract symbols from Python files
- Extracts all top-level functions and classes from a `.py` file
- Extracts methods from classes
- Uses Python `ast` stdlib

### AC-2: Symbol ID format
- Top-level function: `"<module>.<function_name>"`
- Class: `"<module>.<ClassName>"`
- Method: `"<module>.<ClassName>.<method_name>"`
- Module name derived from relative file path (e.g., `mypackage/utils.py` → `mypackage.utils`)

### AC-3: Detect added symbols
- Symbol in migrated but not in original → `change_kind="added"`

### AC-4: Detect deleted symbols
- Symbol in original but not in migrated → `change_kind="deleted"`

### AC-5: Detect body changes
- Symbol in both versions, signature identical, body different → `change_kind="body_changed"`

### AC-6: Detect signature changes
- Function signature (argument names, defaults, return annotation) different → `change_kind="signature_changed"`
- Signature change takes priority over body change

### AC-7: Unchanged symbols excluded
- Symbols with identical source → not in result

### AC-8: Only analyze modified files
- Only process files with `status="modified"` or `status="added"` or `status="deleted"` from FileDiff
- For added files: all symbols are `change_kind="added"`
- For deleted files: all symbols are `change_kind="deleted"`

### AC-9: Function signature
```python
def analyze_symbol_diff(
    file_diffs: list[FileDiff],
    original_dir: Path,
    migrated_dir: Path
) -> list[SymbolDiff]:
    ...
```

### AC-10: All tests pass

---

## Non-Goals

- Do NOT analyze imports (that is TASK-005 / graph builder)
- Do NOT compute call relationships (that is TASK-005)
- Do NOT handle dynamic attribute creation or metaclasses
- Do NOT handle decorators as part of signature comparison (treat decorated functions by their bare signature)

---

## Technical Constraints

- Use Python `ast` stdlib only for parsing
- Use `ast.get_source_segment()` or `ast.unparse()` for source extraction
- Do NOT use `libcst` or Tree-sitter

---

## Algorithm Notes

### Extracting symbols from a file

```python
import ast

def extract_symbols(source: str, module_name: str) -> dict[str, dict]:
    """
    Returns a dict mapping symbol_id → {kind, source, signature, lineno}
    """
    tree = ast.parse(source)
    symbols = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            # Only top-level (parent is Module)
            symbol_id = f"{module_name}.{node.name}"
            symbols[symbol_id] = {
                "kind": SymbolKind.FUNCTION,
                "source": ast.get_source_segment(source, node) or ast.unparse(node),
                "signature": _extract_signature(node),
                "lineno": node.lineno,
            }
        elif isinstance(node, ast.ClassDef):
            class_id = f"{module_name}.{node.name}"
            symbols[class_id] = {
                "kind": SymbolKind.CLASS,
                "source": ast.get_source_segment(source, node) or ast.unparse(node),
                "signature": node.name,
                "lineno": node.lineno,
            }
            # Extract methods
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    method_id = f"{module_name}.{node.name}.{item.name}"
                    symbols[method_id] = {
                        "kind": SymbolKind.METHOD,
                        "source": ast.get_source_segment(source, item) or ast.unparse(item),
                        "signature": _extract_signature(item),
                        "lineno": item.lineno,
                    }

    return symbols
```

Note: Only walk top-level and one level deep (class → method). Do not recurse into nested functions.

### Extracting a function signature

```python
def _extract_signature(node: ast.FunctionDef) -> str:
    """Return a canonical string representation of function arguments."""
    return ast.unparse(node.args)
```

---

## Test Requirements

Add to `backend/tests/test_diff_analyzer.py`:

1. `test_symbol_diff_detects_added_function` — function in migrated only
2. `test_symbol_diff_detects_deleted_function` — function in original only
3. `test_symbol_diff_detects_body_change` — same signature, different body
4. `test_symbol_diff_detects_signature_change` — different argument list
5. `test_symbol_diff_detects_method_change` — method change inside a class
6. `test_symbol_diff_ignores_unchanged_symbol` — identical function → not in result
7. `test_symbol_id_format` — verify `module.ClassName.method_name` format

Use `tmp_path` to write real Python source files.

---

## Verification

```bash
cd backend && pytest tests/test_diff_analyzer.py -v
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
