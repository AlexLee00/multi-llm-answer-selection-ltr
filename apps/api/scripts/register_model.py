# apps/api/scripts/register_model.py
from __future__ import annotations

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ARTIFACTS_DIR = Path("artifacts")
MODELS_DIR = ARTIFACTS_DIR / "models"


def _pick_meta_path() -> Path:
    """
    1) env MODEL_META_PATH가 있으면 그 파일 사용
    2) 없으면 artifacts/models 아래 baseline_lr_*.json 중 최신 파일 사용
    """
    env_path = os.getenv("MODEL_META_PATH")
    if env_path:
        p = Path(env_path)
        if not p.exists():
            raise FileNotFoundError(f"MODEL_META_PATH not found: {p}")
        return p

    metas = sorted(MODELS_DIR.glob("baseline_lr_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not metas:
        raise FileNotFoundError(f"No baseline_lr_*.json found under {MODELS_DIR}")
    return metas[0]


def main() -> None:
    load_dotenv()

    db_url = os.getenv("DB_URL", "").strip()
    if not db_url:
        raise RuntimeError("DB_URL is empty. Set it in apps/api/.env")

    meta_path = _pick_meta_path()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    model_version: str = meta["model_version"]
    snapshot_id: str = meta["snapshot_id"]
    artifact_path: str = meta["artifact_path"]

    metrics: dict = meta["metrics"]
    feature_version: str = metrics.get("feature_version", meta.get("feature_version", "fv1"))

    # ✅ 핵심: dict -> JSON string
    metrics_json_str = json.dumps(metrics, ensure_ascii=False)

    engine = create_engine(db_url, future=True)

    # ✅ 핵심: SQL에서 jsonb 캐스팅
    sql = text(
        """
        insert into models (model_version, snapshot_id, feature_version, metrics_json, artifact_path)
        values (:model_version, :snapshot_id, :feature_version, cast(:metrics_json as jsonb), :artifact_path)
        on conflict (model_version) do update
        set snapshot_id = excluded.snapshot_id,
            feature_version = excluded.feature_version,
            metrics_json = excluded.metrics_json,
            artifact_path = excluded.artifact_path,
            trained_at = now();
        """
    )

    with engine.begin() as conn:
        conn.execute(
            sql,
            {
                "model_version": model_version,
                "snapshot_id": snapshot_id,
                "feature_version": feature_version,
                "metrics_json": metrics_json_str,
                "artifact_path": artifact_path,
            },
        )

    print("✅ Model registered")
    print(f"- model_version : {model_version}")
    print(f"- snapshot_id   : {snapshot_id}")
    print(f"- feature_ver   : {feature_version}")
    print(f"- artifact_path : {artifact_path}")
    print(f"- meta_used     : {meta_path}")


if __name__ == "__main__":
    main()
