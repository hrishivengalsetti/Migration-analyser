from enum import Enum
from typing import Optional, Literal
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

class ComparisonStatus(str, Enum):
    REGRESSION = "regression"
    FIXED = "fixed"
    UNCHANGED = "unchanged"
    ADDED = "added"
    DELETED = "deleted"
    UNVERIFIED = "unverified"

class SymbolTestComparison(BaseModel):
    test_id: str                          # nodeid (e.g. "tests/test_api.py::test_login")
    status_original: Optional[str] = None # "passed" | "failed" | "error" | "skipped" | None
    status_migrated: Optional[str] = None # "passed" | "failed" | "error" | "skipped" | None
    comparison: ComparisonStatus
    stdout_migrated: Optional[str] = None
    stderr_migrated: Optional[str] = None
    message: Optional[str] = None

class BehavioralComparison(BaseModel):
    total_tests: int
    regressions_count: int
    fixed_count: int
    unchanged_count: int
    added_count: int
    deleted_count: int
    unverified_count: int
    test_results: list[SymbolTestComparison]

class Evidence(BaseModel):
    symbol_id: str                                 # e.g. "app.client.HttpClient.post" or "<unattributed>"
    file: str                                      # relative file path or "unattributed"
    change_kind: Optional[SymbolChangeKind] = None # "added" | "deleted" | "body_changed" | "signature_changed" | None
    comparison: ComparisonStatus                   # "regression" | "fixed" | "unchanged" | "added" | "deleted" | "unverified"
    failing_tests: list[str]                       # test nodeids that failed/errored in migrated
    passing_tests: list[str]                       # test nodeids that passed in migrated
    unverified_tests: list[str]                    # test nodeids that were unverified

class AIInterpretation(BaseModel):
    migration_intent: str
    risk_summary: str
    key_concerns: list[str]
    confidence: Literal["high", "medium", "low", "none"]

class Classification(str, Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    REGRESSION_DETECTED = "regression_detected"
    UNVERIFIED = "unverified"

class ReportSummary(BaseModel):
    total_files_changed: int
    total_symbols_changed: int
    total_affected_symbols: int
    total_tests_run: int
    regressions_count: int

class GraphNode(BaseModel):
    id: str
    kind: str
    file: str

class GraphEdge(BaseModel):
    source: str
    target: str
    kind: str

class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

class Report(BaseModel):
    run_id: str
    created_at: str
    classification: Classification
    summary: ReportSummary
    ai_interpretation: AIInterpretation
    file_diffs: list[FileDiff]
    symbol_diffs: list[SymbolDiff]
    blast_radius: BlastRadius
    graph_data: GraphData
    test_results: list[SymbolTestComparison]
    evidence: list[Evidence]

class Run(BaseModel):
    run_id: str
    status: RunStatus
    created_at: str
    error: Optional[str] = None

class CreateRunResponse(BaseModel):
    run_id: str
    status: str
