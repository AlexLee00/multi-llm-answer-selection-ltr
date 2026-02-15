# apps/api/src/app/services/ranker.py
from __future__ import annotations

import os
import json
from typing import Optional, Tuple, List
from pathlib import Path

import joblib
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.app.db.models import Candidate

# ---- cache (process-wide) ----
_MODEL_CACHE: dict[str, object] = {}
_META_CACHE: dict[str, dict] = {}
_ACTIVE_VERSION_CACHE: Optional[str] = None


def _project_root() -> Path:
    """
    Resolve project root in a robust way.
    This file: apps/api/src/app/services/ranker.py
    Root:      apps/api
    """
    return Path(__file__).resolve().parents[3]


def _load_model(artifact_path: str):
    """
    artifact_path can be:
    - absolute path
    - relative path (recommended: artifacts/models/xxx.pkl)
    We resolve relative path from apps/api (project root for api app).
    """
    p = Path(artifact_path)

    if not p.is_absolute():
        p = _project_root() / p

    if not p.exists():
        raise FileNotFoundError(f"Model artifact not found: {str(p)}")

    return joblib.load(str(p))


def _get_active_model_version(db: Session) -> Optional[str]:
    # Option A: ENV pinned
    env_ver = os.getenv("ACTIVE_MODEL_VERSION", "").strip()
    if env_ver:
        return env_ver

    # Option B: newest in DB
    row = db.execute(
        text(
            """
            select model_version
            from models
            order by trained_at desc
            limit 1
            """
        )
    ).fetchone()
    return row[0] if row else None


def _get_model_record(db: Session, model_version: str) -> Optional[tuple[str, dict | str]]:
    row = db.execute(
        text(
            """
            select artifact_path, metrics_json
            from models
            where model_version = :mv
            limit 1
            """
        ),
        {"mv": model_version},
    ).fetchone()
    if not row:
        return None
    return row[0], row[1]


def _parse_metrics(metrics_json: dict | str | None) -> dict:
    if metrics_json is None:
        return {}
    if isinstance(metrics_json, dict):
        return metrics_json
    if isinstance(metrics_json, str):
        try:
            return json.loads(metrics_json)
        except Exception:
            return {"raw": metrics_json}
    return {}


def _features_fv1(c: Candidate) -> np.ndarray:
    """
    fv1 features (same order as training):
    [len_words, has_code, step_score, has_bullets, has_warning]
    """
    return np.array(
        [
            float(c.len_words),
            float(int(bool(c.has_code))),
            float(c.step_score),
            float(int(bool(c.has_bullets))),
            float(int(bool(c.has_warning))),
        ],
        dtype=float,
    )


def _pairwise_diff(a: Candidate, b: Candidate) -> np.ndarray:
    # model was trained on diff = A - B
    return _features_fv1(a) - _features_fv1(b)


def _predict_win_prob(model: object, x: np.ndarray) -> float:
    """
    Return P(y=1) (A wins) for 1xN feature vector.
    - prefer predict_proba
    - fallback to decision_function or predict
    """
    # 1) predict_proba
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x)
        return float(proba[0, 1])

    # 2) decision_function -> sigmoid-ish fallback
    if hasattr(model, "decision_function"):
        score = float(model.decision_function(x)[0])
        return float(1.0 / (1.0 + np.exp(-score)))

    # 3) predict -> treat as hard label
    if hasattr(model, "predict"):
        y = int(model.predict(x)[0])
        return 1.0 if y == 1 else 0.0

    raise TypeError("Model does not support predict_proba/decision_function/predict.")


def ltr_choose_best(
    db: Session,
    candidates: List[Candidate],
) -> Tuple[Optional[Candidate], Optional[str], Optional[str]]:
    """
    Returns: (best_candidate, model_version, error_message)

    - If no model available -> (None, None, "no_model")
    - If no candidates -> (None, mv, "no_candidates")
    - If failure -> (None, mv, "error: ...")
    """
    mv = _get_active_model_version(db)
    if not mv:
        return None, None, "no_model"

    global _ACTIVE_VERSION_CACHE, _MODEL_CACHE, _META_CACHE

    try:
        # Reload if:
        # - first load
        # - active version changed
        # - cache miss
        if mv != _ACTIVE_VERSION_CACHE or mv not in _MODEL_CACHE:
            rec = _get_model_record(db, mv)
            if not rec:
                return None, mv, "model_not_found_in_db"

            artifact_path, metrics_json = rec
            _MODEL_CACHE[mv] = _load_model(artifact_path)
            _META_CACHE[mv] = _parse_metrics(metrics_json)
            _ACTIVE_VERSION_CACHE = mv

        model = _MODEL_CACHE[mv]

        n = len(candidates)
        if n == 0:
            return None, mv, "no_candidates"
        if n == 1:
            return candidates[0], mv, None  # only one -> trivially best

        # tournament scoring:
        # score each candidate by average win probability vs others
        probs: List[float] = []
        for i, a in enumerate(candidates):
            p_list: List[float] = []
            for j, b in enumerate(candidates):
                if i == j:
                    continue
                x = _pairwise_diff(a, b).reshape(1, -1)
                p_list.append(_predict_win_prob(model, x))
            probs.append(float(sum(p_list) / max(1, len(p_list))))

        best_idx = int(np.argmax(probs))
        return candidates[best_idx], mv, None

    except Exception as e:
        return None, mv, f"error: {e}"
