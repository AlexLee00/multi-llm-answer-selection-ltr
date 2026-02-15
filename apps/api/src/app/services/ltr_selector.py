from __future__ import annotations

import joblib
import numpy as np
from pathlib import Path


FEATURES = [
    "len_words_diff",
    "has_code_diff",
    "step_score_diff",
    "has_bullets_diff",
    "has_warning_diff",
]


def _featurize(a: dict, b: dict) -> np.ndarray:
    return np.array(
        [[
            a["len_words"] - b["len_words"],
            int(a["has_code"]) - int(b["has_code"]),
            int(a["step_score"]) - int(b["step_score"]),
            int(a["has_bullets"]) - int(b["has_bullets"]),
            int(a["has_warning"]) - int(b["has_warning"]),
        ]],
        dtype=float,
    )


def pick_winner_with_model(model_path: str, a: dict, b: dict) -> str:
    """
    return: "a" or "b"
    """
    model = joblib.load(Path(model_path))
    X = _featurize(a, b)

    # predict_proba 있으면 1클래스(=a 승) 확률 사용
    if hasattr(model, "predict_proba"):
        p = model.predict_proba(X)[0][1]
        return "a" if p >= 0.5 else "b"

    pred = model.predict(X)[0]
    return "a" if int(pred) == 1 else "b"
