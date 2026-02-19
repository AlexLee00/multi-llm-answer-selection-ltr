# apps/api/src/app/services/llm/engines/dummy_openrouter.py
import time
from ..base import LLMEngine
from ..types import EngineRequest, EngineResult


class DummyOpenRouterEngine(LLMEngine):

    def provider_name(self) -> str:
        return "openrouter"

    def generate(self, request: EngineRequest) -> EngineResult:
        start = time.time()

        user_prompt = (request.params_json or {}).get("_user_prompt", "")
        answer = (
            f"[OpenRouter Dummy - {request.model}]\n"
            f"Step 1: {user_prompt}\n"
            f"Step 2: Example answer from OpenRouter free model."
        )

        return EngineResult(
            provider="openrouter",
            model="dummy-free",
            answer_summary=answer,
            latency_ms=int((time.time() - start) * 1000),
        )
