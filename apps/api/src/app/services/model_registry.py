from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_latest_model(db: Session) -> dict | None:
    row = db.execute(
        text(
            """
            select model_version, feature_version, artifact_path, metrics_json, trained_at
            from models
            order by trained_at desc
            limit 1;
            """
        )
    ).mappings().first()

    return dict(row) if row else None
