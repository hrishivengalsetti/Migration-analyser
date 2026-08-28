# TASK-003: Diff Analyzer — File-Level Diff

**Milestone**: M2  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-002 (complete)  

---

## Goal

Implement the file-level diff analyzer. Given two directory paths (original and migrated), detect which files were added, deleted, modified, or renamed. Produce structured `FileDiff` records. This is Step 1 of the analysis pipeline.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/pipeline/runner.py`
4. `backend/models.py`
5. This task file

---

## Inputs

- `original_dir: Path` — path to unzipped original codebase
- `migrated_dir: Path` — path to unzipped migrated codebase

## Outputs

```
backend/pipeline/diff_analyzer.py   ← New file
backend/tests/test_diff_analyzer.py ← New file
backend/models.py                   ← Updated: add FileDiff model
```

---

## Data Models (add to models.py)

```python
class FileStatus(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"
    RENAMED = "renamed"
    UNCHANGED = "unchanged"

class FileDiff(BaseModel):
    file: str             # relative path from codebase root
    status: FileStatus
    original_content: Optional[str] = None   # None if added
    migrated_content: Optional[str] = None   # None if deleted
```

---

## Acceptance Criteria

### AC-1: Detect added files
- Files present in `migrated/` but not in `original/` are returned as `status="added"`

### AC-2: Detect deleted files
- Files present in `original/` but not in `migrated/` are returned as `status="deleted"`

### AC-3: Detect modified files
- Files present in both but with different content are returned as `status="modified"`
- `original_content` and `migrated_content` are populated with the file's text content

### AC-4: Unchanged files excluded
- Files with identical content are NOT included in the result

### AC-5: Only Python files
- Only analyze files with `.py` extension
- Ignore: `__pycache__/`, `.pyc` files, `.git/`, hidden directories

### AC-6: Relative paths
- The `file` field contains the path relative to the codebase root directory (e.g., `"mypackage/utils.py"`)

### AC-7: Function signature
```python
def analyze_file_diff(original_dir: Path, migrated_dir: Path) -> list[FileDiff]:
    ...
```

### AC-8: All tests pass
- `cd backend && pytest tests/test_diff_analyzer.py -v` exits with code 0

---

## Non-Goals

- Do NOT detect renames (too complex for MVP; treat rename as delete + add)
- Do NOT analyze non-Python files
- Do NOT compute line-level diffs or hunks (that is cosmetic for the frontend, not needed for analysis)
- Do NOT integrate into the pipeline runner yet (that happens after TASK-004)

---

## Technical Constraints

- Use Python stdlib only: `pathlib`, `filecmp`, `os`
- Do NOT use `subprocess` or `git diff`
- Do NOT use external libraries

---

## Algorithm

```python
from pathlib import Path

def analyze_file_diff(original_dir: Path, migrated_dir: Path) -> list[FileDiff]:
    diffs = []

    original_files = {
        p.relative_to(original_dir): p
        for p in original_dir.rglob("*.py")
        if not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    }

    migrated_files = {
        p.relative_to(migrated_dir): p
        for p in migrated_dir.rglob("*.py")
        if not any(part.startswith('.') or part == '__pycache__' for part in p.parts)
    }

    all_keys = set(original_files) | set(migrated_files)

    for rel_path in sorted(all_keys):
        if rel_path in original_files and rel_path not in migrated_files:
            # deleted
            diffs.append(FileDiff(
                file=str(rel_path),
                status=FileStatus.DELETED,
                original_content=original_files[rel_path].read_text(errors='replace'),
            ))
        elif rel_path not in original_files and rel_path in migrated_files:
            # added
            diffs.append(FileDiff(
                file=str(rel_path),
                status=FileStatus.ADDED,
                migrated_content=migrated_files[rel_path].read_text(errors='replace'),
            ))
        else:
            # both exist — compare
            orig_content = original_files[rel_path].read_text(errors='replace')
            migr_content = migrated_files[rel_path].read_text(errors='replace')
            if orig_content != migr_content:
                diffs.append(FileDiff(
                    file=str(rel_path),
                    status=FileStatus.MODIFIED,
                    original_content=orig_content,
                    migrated_content=migr_content,
                ))

    return diffs
```

You may implement this exactly as shown, or vary the implementation as long as all ACs pass.

---

## Test Requirements

Write tests in `backend/tests/test_diff_analyzer.py`:

Use `tmp_path` fixture to create real directories.

1. `test_detects_added_file` — file in migrated only → status "added"
2. `test_detects_deleted_file` — file in original only → status "deleted"
3. `test_detects_modified_file` — same file, different content → status "modified", both contents populated
4. `test_ignores_unchanged_file` — identical files → not in result
5. `test_only_python_files` — add a `.txt` file → not in result
6. `test_ignores_pycache` — file in `__pycache__/` → not in result
7. `test_relative_paths` — returned paths are relative to codebase root

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
