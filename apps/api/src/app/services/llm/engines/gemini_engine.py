# apps/api/src/app/services/llm/engines/gemini_engine.py
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from src.app.services.llm.base import LLMEngine
from src.app.services.llm.types import EngineRequest, EngineResult


class GeminiEngine(LLMEngine):
    """
    Real Gemini engine (google-genai SDK).
    - Server must boot even if 'google-genai' is not installed.
    - If GEMINI_API_KEY missing -> returns EngineResult.error (no exception)
    - system_prompt → prepended to user_prompt (Gemini does not support system role)
    """

    def provider_name(self) -> str:
        return "gemini"

    def generate(self, request: EngineRequest) -> EngineResult:
        t0 = time.time()

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary="",
                latency_ms=int((time.time() - t0) * 1000),
                error="missing_env:GEMINI_API_KEY",
            )

        # --- lazy import (prevents ModuleNotFoundError on server boot) ---
        try:
            from google import genai  # type: ignore
            from google.genai import types as genai_types  # type: ignore
        except Exception as e:
            return EngineResult(
                provider=self.provider_name(),
                model=request.model,
                answer_summary="",
                latency_ms=int((time.time() - t0) * 1000),
                error=f"gemini_import_error:{repr(e)}",
            )

        # params
        params: Dict[str, Any] = request.params_json or {}
        temperature = float(params.get("temperature", 0.2))
        max_tokens = int(params.get("max_tokens", 512))

        system_prompt = str(params.get("_system_prompt", ""))
        user_prompt = str(params.get("_user_prompt", ""))

        # Gemini는 system role을 직접 지원하지 않으므로
        # system_prompt를 user_prompt 앞에 prepend 한다.
        full_prompt = f"{system_prompt}\n\n{user_prompt}".strip() if system_prompt else user_prompt

        try:
            client = genai.Client(api_key=api_key)

            config = genai_types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            resp = client.models.generate_content(
                model=request.model,
                contents=full_prompt,
                config=config,
            )

            text = resp.text or ""
            latency_ms = int((time.time() - t0) * 1000)

            # token fields (best-effort)
            tokens_in: Optional[int] = None
            tokens_out: Optional[int] = None
            try:
                meta = resp.usage_metadata
                if meta:
                    tokens_in = int(getattr(meta, "prompt_token_count", 0) or 0)
                    tokens_out = int(getattr(meta, "candidates_token_count", 0) or 0)
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
                error=f"gemini_call_error:{repr(e)}",
            )
