# apps/api/src/app/services/generator.py
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from src.app.services.llm.types import EngineRequest
from src.app.services.llm.registry import build_default_registry
from src.app.services.llm.orchestrator import run_sequential
from src.app.services.llm.prompt_builder import build_prompts_v1


def _mk_req(
    *,
    provider: str,
    model: str,
    question: str,
    role: str,
    level: str,
    goal: str,
    stack: str,
    constraints: str,
    domain: str,
    params_json: Optional[Dict[str, Any]] = None,
    timeout_s: float = 20.0,
) -> EngineRequest:
    rid = str(uuid.uuid4())
    pj = dict(params_json or {})
    pj["_question"] = question  # prompt_builder에서 사용
    req = EngineRequest(
        request_id=rid,
        role=role,
        level=level,
        goal=goal,
        stack=stack,
        constraints=constraints,
        domain=domain,
        provider=provider,
        model=model,
        params_json=pj,
        timeout_s=timeout_s,
    )
    return req


def generate_candidates_v1(
    *,
    question: str,
    role: str,
    level: str,
    goal: str,
    stack: str,
    constraints: str,
    domain: str,
) -> List[Dict[str, Any]]:
    """
    Always returns 2 candidates (pads failures with error results).
    """

    reg = build_default_registry()

    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite").strip()
    openrouter_model = os.getenv(
        "OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free"
    ).strip()

    openai_timeout = float(os.getenv("OPENAI_TIMEOUT_S", "20"))
    gemini_timeout = float(os.getenv("GEMINI_TIMEOUT_S", "20"))
    openrouter_timeout = float(os.getenv("OPENROUTER_TIMEOUT_S", "30"))

    # ENABLED_ENGINES 환경변수로 어떤 엔진을 실제로 호출할지 결정
    # 예: ENABLED_ENGINES=openrouter,gemini  (openai는 더미로 유지)
    enabled_engines_raw = os.getenv("ENABLED_ENGINES", "openai,gemini").strip()
    enabled_engines = [e.strip() for e in enabled_engines_raw.split(",") if e.strip()]

    # 엔진별 요청 빌더 맵
    engine_req_map = {
        "openai": _mk_req(
            provider="openai",
            model=openai_model,
            question=question,
            role=role,
            level=level,
            goal=goal,
            stack=stack,
            constraints=constraints,
            domain=domain,
            params_json={"temperature": 0.2, "max_tokens": 512},
            timeout_s=openai_timeout,
        ),
        "gemini": _mk_req(
            provider="gemini",
            model=gemini_model,
            question=question,
            role=role,
            level=level,
            goal=goal,
            stack=stack,
            constraints=constraints,
            domain=domain,
            params_json={"temperature": 0.2, "max_tokens": 512},
            timeout_s=gemini_timeout,
        ),
        "openrouter": _mk_req(
            provider="openrouter",
            model=openrouter_model,
            question=question,
            role=role,
            level=level,
            goal=goal,
            stack=stack,
            constraints=constraints,
            domain=domain,
            params_json={"temperature": 0.2, "max_tokens": 512},
            timeout_s=openrouter_timeout,
        ),
    }

    reqs = [engine_req_map[e] for e in enabled_engines if e in engine_req_map]

    # prompt injection into params_json for engines
    for r in reqs:
        system_prompt, user_prompt = build_prompts_v1(r)
        r.params_json = dict(r.params_json or {})
        r.params_json["_system_prompt"] = system_prompt
        r.params_json["_user_prompt"] = user_prompt

    results = run_sequential(reg, reqs)

    # convert to candidate dicts (keep failures)
    out: List[Dict[str, Any]] = []
    for res in results:
        out.append(
            {
                "provider": res.provider,
                "model": res.model,
                "answer_summary": res.answer_summary or "",
                "latency_ms": res.latency_ms,
                "tokens_in": res.tokens_in,
                "tokens_out": res.tokens_out,
                "error": res.error,
                "params_json": {},  # 저장 필요하면 여기에
                # 아래 3개는 기존 feature 스키마에 맞춰 optional
                "has_code": False,
                "has_bullets": False,
                "has_warning": False,
            }
        )

    # pad to 2 (defensive)
    while len(out) < 2:
        out.append(
            {
                "provider": "fallback",
                "model": "fallback",
                "answer_summary": "",
                "latency_ms": 0,
                "tokens_in": None,
                "tokens_out": None,
                "error": "padded_fallback",
                "params_json": {},
                "has_code": False,
                "has_bullets": False,
                "has_warning": False,
            }
        )

    return out[:2]
