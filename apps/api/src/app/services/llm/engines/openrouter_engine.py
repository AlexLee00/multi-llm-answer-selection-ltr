# apps/api/src/app/services/llm/engines/openrouter_engine.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from src.app.services.llm.base import LLMEngine
from src.app.services.llm.types import EngineRequest, EngineResult

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterEngine(LLMEngine):
    """
    OpenRouter engine — OpenAI-compatible API.
    - 무료 모델(예: deepseek/deepseek-chat-v3-0324:free) 사용 가능
    - openai SDK를 재사용하고 base_url만 OpenRouter로 변경
    - OPENROUTER_API_KEY 환경변수가 없으면 error 반환 (서버는 정상 기동)
    """

    def provider_name(self) -> str:
        return "openrouter"

    def generate(self, request: EngineRequest) -> EngineResult:
        t0 = time.time()

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary="",
                latency_ms=int((time.time() - t0) * 1000),
                error="missing_env:OPENROUTER_API_KEY",
            )

        # openai SDK를 이용해 OpenRouter endpoint 호출
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary="",
                latency_ms=int((time.time() - t0) * 1000),
                error=f"openrouter_import_error:{repr(e)}",
            )

        params: Dict[str, Any] = request.params_json or {}
        temperature = float(params.get("temperature", 0.2))
        max_tokens = int(params.get("max_tokens", 512))

        system_prompt = str(params.get("_system_prompt", ""))
        user_prompt = str(params.get("_user_prompt", ""))

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=_OPENROUTER_BASE_URL,
            )

            resp = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers={
                    # OpenRouter 권장 헤더 (optional)
                    "HTTP-Referer": "https://github.com/multi-llm-answer-selection-ltr",
                    "X-Title": "Multi-LLM Answer Selection",
                },
            )

            text = resp.choices[0].message.content or ""
            latency_ms = int((time.time() - t0) * 1000)

            tokens_in: Optional[int] = None
            tokens_out: Optional[int] = None
            try:
                if resp.usage:
                    tokens_in = int(getattr(resp.usage, "prompt_tokens", 0) or 0)
                    tokens_out = int(getattr(resp.usage, "completion_tokens", 0) or 0)
            except Exception:
                pass

            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary=text.strip(),
                latency_ms=latency_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                error=None,
            )

        except Exception as e:
            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary="",
                latency_ms=int((time.time() - t0) * 1000),
                error=f"openrouter_call_error:{repr(e)}",
            )
