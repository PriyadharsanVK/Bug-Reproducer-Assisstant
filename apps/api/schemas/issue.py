from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class IssueSource(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    MANUAL = "manual"

class IssueIngestRequest(BaseModel):
    source: IssueSource = Field(..., example="github")
    source_id: Optional[str] = Field(None, example="GH-101")
    repository_url: Optional[str] = Field(None, example="https://github.com/org/repo")
    title: str = Field(..., example="TypeError: 'NoneType' object is not subscriptable in token handler")
    body: str = Field(..., example="When sending empty payload scope=[] to POST /token endpoint, service crashes.")
    raw_logs: Optional[str] = Field(None, example="Traceback (most recent call last):\n  File 'auth.py', line 42...")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IssueIngestResponse(BaseModel):
    issue_id: str
    status: str = "ingested"
    created_at: datetime
