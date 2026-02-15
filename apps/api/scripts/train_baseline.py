# apps/api/scripts/train_baseline.py
from __future__ import annotations

import os
import json
import glob
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, roc_auc_score


ARTIFACTS_DIR = Path("artifacts")
TRAINSETS_DIR = ARTIFACTS_DIR / "trainsets"
MODELS_DIR = ARTIFACTS_DIR / "models"


FEATURE_COLS_A = ["a_len_words", "a_has_code", "a_step_score", "a_has_bullets", "a_has_warning"]
FEATURE_COLS_B = ["b_len_words", "b_has_code", "b_step_score", "b_has_bullets", "b_has_warning"]


@dataclass
class TrainResult:
    model_version: str
    snapshot_id: str
    artifact_path: str
    metrics: dict


def _utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _pick_trainset_path() -> Path:
    # 1) explicit env
    env_path = os.getenv("TRAINSET_PATH")
    if env_path:
        p = Path(env_path)
        if not p.exists():
            raise FileNotFoundError(f"TRAINSET_PATH not found: {p}")
        return p

    # 2) latest csv in artifacts/trainsets
    candidates = sorted(TRAINSETS_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No trainset csv found under {TRAINSETS_DIR}")
    return candidates[0]


def _infer_snapshot_id(trainset_path: Path) -> str:
    # files are named like <snapshot_id>.csv
    return trainset_path.stem


def _ensure_dirs() -> None:
    TRAINSETS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _coerce_bool_int(series: pd.Series) -> pd.Series:
    # handle "t/f", True/False, 0/1
    if series.dtype == bool:
        return series.astype(int)
    s = series.astype(str).str.lower().map({"true": 1, "false": 0, "t": 1, "f": 0})
    # if mapping fails, try numeric
    return s.fillna(pd.to_numeric(series, errors="coerce")).fillna(0).astype(int)


def _build_X_y(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    # Validate columns
    required = set(FEATURE_COLS_A + FEATURE_COLS_B + ["candidate_a_id", "winner_candidate_id"])
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Trainset missing required columns: {sorted(missing)}")

    # Coerce feature types
    work = df.copy()

    # booleans to int
    for c in ["a_has_code", "a_has_bullets", "a_has_warning", "b_has_code", "b_has_bullets", "b_has_warning"]:
        work[c] = _coerce_bool_int(work[c])

    # numeric
    for c in ["a_len_words", "a_step_score", "b_len_words", "b_step_score"]:
        work[c] = pd.to_numeric(work[c], errors="coerce").fillna(0).astype(int)

    # Build diff features: A - B
    X = np.column_stack(
        [
            (work["a_len_words"] - work["b_len_words"]).to_numpy(),
            (work["a_has_code"] - work["b_has_code"]).to_numpy(),
            (work["a_step_score"] - work["b_step_score"]).to_numpy(),
            (work["a_has_bullets"] - work["b_has_bullets"]).to_numpy(),
            (work["a_has_warning"] - work["b_has_warning"]).to_numpy(),
        ]
    )

    # Label: 1 if winner == A else 0
    y = (work["winner_candidate_id"].astype(str) == work["candidate_a_id"].astype(str)).astype(int).to_numpy()
    return X, y


def _train_model(X: np.ndarray, y: np.ndarray):
    classes = np.unique(y)
    if len(classes) < 2:
        # fallback for tiny data
        model = DummyClassifier(strategy="most_frequent")
        model.fit(X, y)
        return model

    model = LogisticRegression(
        max_iter=200,
        class_weight="balanced",
        solver="liblinear",
        random_state=42,
    )
    model.fit(X, y)
    return model


def main() -> None:
    _ensure_dirs()

    trainset_path = _pick_trainset_path()
    snapshot_id = _infer_snapshot_id(trainset_path)

    print(f"Using trainset: {trainset_path}")
    df = pd.read_csv(trainset_path)
    print(f"raw rows: {len(df)}")

    # Keep only winner-labeled rows (already should be filtered by export)
    df = df.dropna(subset=["winner_candidate_id"])
    print(f"rows after winner filter: {len(df)}")
    if len(df) < 2:
        raise RuntimeError("Not enough rows to train. Need at least 2.")

    X, y = _build_X_y(df)
    classes, counts = np.unique(y, return_counts=True)
    print(f"class distribution: {dict(zip(classes.tolist(), counts.tolist()))}")

    # Split
    test_size = float(os.getenv("VALID_RATIO", "0.25"))
    test_size = min(max(test_size, 0.1), 0.5)

    # Stratify only if both classes exist
    stratify = y if len(np.unique(y)) >= 2 else None
    X_train, X_valid, y_train, y_valid = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify
    )

    model = _train_model(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_valid)
    acc = float(accuracy_score(y_valid, y_pred))

    # AUC only meaningful if valid set has both classes
    auc: Optional[float] = None
    if len(np.unique(y_valid)) >= 2 and hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_valid)[:, 1]
        auc = float(roc_auc_score(y_valid, proba))

    # Save artifacts
    model_version = f"baseline_lr_{_utc_now_compact()}"
    model_path = MODELS_DIR / f"{model_version}.pkl"
    meta_path = MODELS_DIR / f"{model_version}.json"

    joblib.dump(model, model_path)

    metrics = {
        "accuracy": acc,
        "roc_auc": auc,
        "n_rows_total": int(len(df)),
        "n_train": int(len(y_train)),
        "n_valid": int(len(y_valid)),
        "class_counts_total": {str(int(k)): int(v) for k, v in zip(classes, counts)},
        "feature_version": "fv1",
        "features": ["len_words_diff", "has_code_diff", "step_score_diff", "has_bullets_diff", "has_warning_diff"],
    }

    meta = {
        "model_version": model_version,
        "snapshot_id": snapshot_id,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "trainset_path": str(trainset_path).replace("\\", "/"),
        "artifact_path": str(model_path).replace("\\", "/"),
        "metrics": metrics,
    }

    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print("✅ Training complete")
    print(f"- model_version : {model_version}")
    print(f"- accuracy      : {acc}")
    print(f"- roc_auc       : {auc}")
    print(f"- saved model   : {model_path}")
    print(f"- saved meta    : {meta_path}")


if __name__ == "__main__":
    main()
