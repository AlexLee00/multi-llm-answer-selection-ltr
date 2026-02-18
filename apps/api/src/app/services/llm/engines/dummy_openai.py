# apps/api/src/app/services/llm/engines/dummy_openai.py
import time
from ..base import LLMEngine
from ..types import EngineRequest, EngineResult


class DummyOpenAIEngine(LLMEngine):

    def provider_name(self) -> str:
        return "openai"

    def generate(self, request: EngineRequest) -> EngineResult:
        start = time.time()

        user_prompt = (request.params_json or {}).get("_user_prompt", "")
        answer = f"[OpenAI Dummy]\nStep 1: {user_prompt}\nStep 2: Example explanation."

        latency = int((time.time() - start) * 1000)

        return EngineResult(
            provider="openai",
            model="gpt-dummy",
            answer_summary=answer,
            latency_ms=latency,
        )
