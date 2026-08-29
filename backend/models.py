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
