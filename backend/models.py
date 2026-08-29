from enum import Enum
from typing import Optional
from pydantic import BaseModel

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

class BlastRadius(BaseModel):
    changed_symbols: list[str]
    directly_affected: list[str]
    transitively_affected: list[str]
    all_affected: list[str]
    cycles_detected: bool
    total_affected_count: int

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

class CreateRunResponse(BaseModel):
    run_id: str
    status: str
