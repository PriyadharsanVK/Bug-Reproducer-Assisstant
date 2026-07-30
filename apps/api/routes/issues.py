from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from apps.api.db.session import get_db
from apps.api.db.models import Issue, IssueSourceEnum
from apps.api.schemas.issue import IssueIngestRequest, IssueIngestResponse

router = APIRouter(prefix="/issues", tags=["Issues"])

@router.post("/ingest", response_model=IssueIngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_issue(payload: IssueIngestRequest, db: AsyncSession = Depends(get_db)):
    try:
        issue = Issue(
            source=IssueSourceEnum(payload.source.value),
            source_id=payload.source_id,
            repository_url=payload.repository_url,
            title=payload.title,
            body=payload.body,
            raw_logs=payload.raw_logs,
            metadata_json=payload.metadata
        )
        db.add(issue)
        await db.commit()
        await db.refresh(issue)

        return IssueIngestResponse(
            issue_id=str(issue.id),
            status="ingested",
            created_at=issue.created_at
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to ingest issue: {str(e)}")
