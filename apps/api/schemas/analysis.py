from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AnalysisStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_INPUT = "needs_input"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisRunRequest(BaseModel):
    issue_id: str
    auto_execute_sandbox: bool = True

class AnalysisRunResponse(BaseModel):
    run_id: str
    issue_id: str
    status: AnalysisStatus
    overall_confidence: Optional[float] = None
    created_at: datetime
    error_message: Optional[str] = None

class ClarificationAnswer(BaseModel):
    question_id: str
    target_field: str
    answer: str

class ClarificationSubmitRequest(BaseModel):
    answers: List[ClarificationAnswer]

class ClarificationQuestion(BaseModel):
    """A single pending clarification question returned by GET /clarifications."""
    question_id: str
    target_field: str          # the raw unknown name, e.g. "error_message"
    question: str              # human-readable question text
    options: List[str] = []   # optional multiple-choice hints (may be empty)

class ClarificationListResponse(BaseModel):
    """Response for GET /analysis/{run_id}/clarifications."""
    run_id: str
    status: str
    questions: List[ClarificationQuestion]

class FeedbackRequest(BaseModel):
    developer_rating: int = Field(..., ge=1, le=5)
    repro_successful: bool
    comments: Optional[str] = None
