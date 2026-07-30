import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from apps.api.db.session import get_db
from apps.api.db.models import AnalysisRun
from apps.api.schemas.analysis import FeedbackRequest

router = APIRouter(prefix="/feedback", tags=["Feedback"])

@router.post("/{run_id}", status_code=status.HTTP_201_CREATED)
async def submit_feedback(run_id: str, payload: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    try:
        run_uuid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format for run_id")

    result = await db.execute(select(AnalysisRun).where(AnalysisRun.id == run_uuid))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found")

    # In production, save to feedback_events table
    return {"status": "recorded", "run_id": run_id, "rating": payload.developer_rating}
