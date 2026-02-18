# apps/api/src/app/services/llm/orchestrator.py
from __future__ import annotations

import time
from typing import List

from src.app.services.llm.registry import EngineRegistry
from src.app.services.llm.types import EngineRequest, EngineResult


def run_sequential(registry: EngineRegistry, requests: List[EngineRequest]) -> List[EngineResult]:
    """
    Sequential execution (v0) with per-request timeout_s handled by engine-call level.
    Engines here are sync; timeout enforcement is best-effort (engine should respect).
    """
    results: List[EngineResult] = []

    for req in requests:
        engine = registry.get(req.provider)
        if engine is None:
            results.append(
                EngineResult(
                    provider=req.provider,
                    model=req.model,
                    answer_summary="",
                    latency_ms=0,
                    error=f"engine_not_registered:{req.provider}",
                )
            )
            continue

        t0 = time.time()
        res = engine.generate(req)
        # if engine didn't set latency, keep its value; otherwise best-effort
        if res.latency_ms <= 0:
            res.latency_ms = int((time.time() - t0) * 1000)
        results.append(res)

    return results


def any_success(results: List[EngineResult]) -> bool:
    return any((r.error is None) and (r.answer_summary.strip() != "") for r in results)
