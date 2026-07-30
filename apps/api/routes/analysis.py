import uuid
import os
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apps.api.db.session import get_db
from apps.api.db.models import AnalysisRun, Issue, AnalysisStatusEnum, Report, Clarification
from apps.api.schemas.analysis import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    ClarificationSubmitRequest,
    ClarificationQuestion,
    ClarificationListResponse,
    AnalysisStatus
)
from apps.worker.tasks.run_analysis import _async_run_pipeline

router = APIRouter(prefix="/analysis", tags=["Analysis"])

@router.post("/run", response_model=AnalysisRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis_run(payload: AnalysisRunRequest, db: AsyncSession = Depends(get_db)):
    try:
        issue_uuid = uuid.UUID(payload.issue_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format for issue_id")

    result = await db.execute(select(Issue).where(Issue.id == issue_uuid))
    issue = result.scalars().first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    run = AnalysisRun(
        issue_id=issue.id,
        status=AnalysisStatusEnum.QUEUED,
        groq_primary_model=os.getenv("GROQ_MODEL_PRIMARY", "llama-3.3-70b-versatile"),
        groq_fast_model=os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant"),
        groq_code_model=os.getenv("GROQ_MODEL_CODE", "deepseek-r1-distill-llama-70b")
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Use asyncio.create_task for instant execution without waiting for Celery/Redis connection retries
    asyncio.create_task(_async_run_pipeline(str(run.id)))

    return AnalysisRunResponse(
        run_id=str(run.id),
        issue_id=str(run.issue_id),
        status=AnalysisStatus(run.status.value),
        created_at=run.created_at
    )

@router.get("/{run_id}", response_model=AnalysisRunResponse)
async def get_analysis_status(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format for run_id")

    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_uuid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    return AnalysisRunResponse(
        run_id=str(run.id),
        issue_id=str(run.issue_id),
        status=AnalysisStatus(run.status.value),
        overall_confidence=float(run.overall_confidence) if run.overall_confidence else None,
        created_at=run.created_at,
        error_message=run.error_message
    )

@router.get("/{run_id}/clarifications", response_model=ClarificationListResponse)
async def get_clarifications(run_id: str, db: AsyncSession = Depends(get_db)):
    """Return the list of pending (unanswered) clarification questions for a run."""
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format for run_id")

    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_uuid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    # Fetch clarification rows that have not yet been answered
    clari_result = await db.execute(
        select(Clarification).where(
            Clarification.run_id == run_uuid,
            Clarification.answer.is_(None)
        ).order_by(Clarification.created_at)
    )
    rows = clari_result.scalars().all()

    questions: list[ClarificationQuestion] = []
    for row in rows:
        # target_field is stored in options[0]["target_field"] (new rows)
        # Fall back to parsing the question text for older rows that used options=[]
        opts = row.options or []
        if opts and isinstance(opts[0], dict):
            target_field = opts[0].get("target_field", row.question_id)
        else:
            # Legacy fallback: "Please provide more information about: {field}"
            prefix = "Please provide more information about: "
            target_field = row.question[len(prefix):] if row.question.startswith(prefix) else row.question_id

        questions.append(ClarificationQuestion(
            question_id=row.question_id,
            target_field=target_field,
            question=row.question,
            options=[]
        ))

    return ClarificationListResponse(
        run_id=run_id,
        status=run.status.value,
        questions=questions
    )


@router.post("/{run_id}/clarifications", response_model=AnalysisRunResponse)
async def submit_clarifications(
    run_id: str,
    payload: ClarificationSubmitRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format for run_id")

    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_uuid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    for ans in payload.answers:
        # Mark any existing unanswered clarification row for this question as answered
        existing_result = await db.execute(
            select(Clarification).where(
                Clarification.run_id == run.id,
                Clarification.question_id == ans.question_id,
                Clarification.answer.is_(None)
            )
        )
        existing_row = existing_result.scalars().first()
        if existing_row:
            existing_row.answer = ans.answer
            existing_row.answered_at = datetime.now(timezone.utc)
        else:
            # No pre-existing row (e.g. direct API call) — create a new one
            clarification = Clarification(
                run_id=run.id,
                question_id=ans.question_id,
                question=f"Target: {ans.target_field}",
                answer=ans.answer,
                answered_at=datetime.now(timezone.utc),
                options=[{"target_field": ans.target_field}]
            )
            db.add(clarification)

    # Resume analysis execution
    run.status = AnalysisStatusEnum.RUNNING
    await db.commit()
    await db.refresh(run)

    asyncio.create_task(_async_run_pipeline(str(run.id)))

    return AnalysisRunResponse(
        run_id=str(run.id),
        issue_id=str(run.issue_id),
        status=AnalysisStatus(run.status.value),
        created_at=run.created_at
    )

@router.get("/{run_id}/report.md")
async def get_report_markdown(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Report).where(Report.run_id == run_uuid))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not generated yet or run failed")

    return Response(content=report.markdown_content, media_type="text/markdown")

@router.get("/{run_id}/report.json")
async def get_report_json(run_id: str, db: AsyncSession = Depends(get_db)):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Report).where(Report.run_id == run_uuid))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not generated yet or run failed")

    return report.json_content
