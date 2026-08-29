from enum import Enum
from typing import Optional
from pydantic import BaseModel

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
