# apps/api/src/app/routers/admin.py
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.app.dependencies import get_db
from src.app.db.models import FeedbackPairwise, Selection, ModelRegistry

router = APIRouter()


# ──────────────────────────────────────────────
# Response schemas
# ──────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_feedbacks: int
    today_feedbacks: int
    rule_served: int
    ltr_served: int


class ModelRecord(BaseModel):
    model_version: str
    feature_version: str
    metrics_json: dict
    artifact_path: str
    trained_at: datetime


# ──────────────────────────────────────────────
# GET /admin/stats
# ──────────────────────────────────────────────

@router.get("/admin/stats", response_model=StatsResponse, tags=["admin"])
def get_stats(db: Session = Depends(get_db)):
    """
    Research Console 용 간단 통계.
    - total_feedbacks: 전체 feedback_pairwise 수
    - today_feedbacks: 오늘(UTC) feedback 수
    - rule_served: selections 중 served_policy='rule' 수
    - ltr_served: selections 중 served_policy='ltr' 수
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    total_feedbacks: int = db.scalar(
        select(func.count()).select_from(FeedbackPairwise)
    ) or 0

    today_feedbacks: int = db.scalar(
        select(func.count())
        .select_from(FeedbackPairwise)
        .where(FeedbackPairwise.created_at >= today_start)
    ) or 0

    rule_served: int = db.scalar(
        select(func.count())
        .select_from(Selection)
        .where(Selection.served_policy == "rule")
    ) or 0

    ltr_served: int = db.scalar(
        select(func.count())
        .select_from(Selection)
        .where(Selection.served_policy == "ltr")
    ) or 0

    return StatsResponse(
        total_feedbacks=total_feedbacks,
        today_feedbacks=today_feedbacks,
        rule_served=rule_served,
        ltr_served=ltr_served,
    )


# ──────────────────────────────────────────────
# GET /admin/models
# ──────────────────────────────────────────────

@router.get("/admin/models", response_model=list[ModelRecord], tags=["admin"])
def get_models(db: Session = Depends(get_db)):
    """
    등록된 LTR 모델 버전 목록 (최신순).
    Research Console의 Active Model Version dropdown 용.
    """
    rows = db.execute(
        select(ModelRegistry).order_by(ModelRegistry.trained_at.desc())
    ).scalars().all()

    return [
        ModelRecord(
            model_version=r.model_version,
            feature_version=r.feature_version,
            metrics_json=r.metrics_json,
            artifact_path=r.artifact_path,
            trained_at=r.trained_at,
        )
        for r in rows
    ]
