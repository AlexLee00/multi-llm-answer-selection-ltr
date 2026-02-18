# apps/api/src/app/services/llm/types.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class EngineRequest:
    # request metadata
    request_id: str
    role: str
    level: str
    goal: str
    stack: str
    constraints: str
    domain: str

    # engine targeting
    provider: str
    model: str

    # runtime config
    params_json: Optional[Dict[str, Any]] = None
    timeout_s: float = 20.0


@dataclass
class EngineResult:
    provider: str
    model: str
    answer_summary: str
    latency_ms: int
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    error: Optional[str] = None
