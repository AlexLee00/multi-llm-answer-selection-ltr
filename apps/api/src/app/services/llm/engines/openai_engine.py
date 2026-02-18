# apps/api/src/app/services/llm/engines/openai_engine.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from src.app.services.llm.base import LLMEngine
from src.app.services.llm.types import EngineRequest, EngineResult


class OpenAIEngine(LLMEngine):
    """
    Real OpenAI engine (lazy import).
    - Server must boot even if 'openai' is not installed.
    - If OPENAI_API_KEY missing -> returns EngineResult.error
    """

    def provider_name(self) -> str:
        return "openai"

    def generate(self, request: EngineRequest) -> EngineResult:
        t0 = time.time()

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary="",
                latency_ms=int((time.time() - t0) * 1000),
                error="missing_env:OPENAI_API_KEY",
            )

        # --- lazy import (prevents ModuleNotFoundError on server boot) ---
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary="",
                latency_ms=int((time.time() - t0) * 1000),
                error=f"openai_import_error:{repr(e)}",
            )

        # params
        params: Dict[str, Any] = request.params_json or {}
        temperature = float(params.get("temperature", 0.2))
        max_tokens = int(params.get("max_tokens", 512))

        # prompts should already be built in prompt_builder
        # 여기서는 system/user prompt를 params로 전달받는 방식 대신
        # prompt_builder가 만든 system/user 문자열을 params에 넣어 전달하는 방식을 쓴다.
        system_prompt = str(params.get("_system_prompt", ""))
        user_prompt = str(params.get("_user_prompt", ""))

        try:
            client = OpenAI(api_key=api_key)

            resp = client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            text = resp.choices[0].message.content or ""
            latency_ms = int((time.time() - t0) * 1000)

            # token fields (best-effort)
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
                error=f"openai_call_error:{repr(e)}",
            )
