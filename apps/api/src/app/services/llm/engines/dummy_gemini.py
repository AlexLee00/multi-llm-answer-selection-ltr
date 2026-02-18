# apps/api/src/app/services/llm/engines/dummy_gemini.py
import time
from ..base import LLMEngine
from ..types import EngineRequest, EngineResult


class DummyGeminiEngine(LLMEngine):

    def provider_name(self) -> str:
        return "gemini"

    def generate(self, request: EngineRequest) -> EngineResult:
        start = time.time()

        user_prompt = (request.params_json or {}).get("_user_prompt", "")
        answer = f"[Gemini Dummy]\n• {user_prompt}\n• Alternative explanation."

        latency = int((time.time() - start) * 1000)

        return EngineResult(
            provider="gemini",
            model="gemini-dummy",
            answer_summary=answer,
            latency_ms=latency,
        )
