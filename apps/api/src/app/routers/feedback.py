from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.app.dependencies import get_db
from src.app.schemas import FeedbackRequest, FeedbackResponse
from src.app.db.models import FeedbackPairwise

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    try:
        fb = FeedbackPairwise(
            question_id=request.question_id,
            candidate_a_id=request.candidate_a_id,
            candidate_b_id=request.candidate_b_id,
            user_choice=request.user_choice,
            reason_tags=request.reason_tags,
            note=request.note,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

        return FeedbackResponse(feedback_id=fb.feedback_id)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
