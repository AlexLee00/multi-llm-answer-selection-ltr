# apps/api/src/app/services/llm/registry.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from src.app.services.llm.base import LLMEngine
from src.app.services.llm.engines.dummy_openai import DummyOpenAIEngine
from src.app.services.llm.engines.dummy_gemini import DummyGeminiEngine

# OpenAIEngine은 lazy import가 되더라도, registry import 시점에 import 에러 나면 안 되므로
# 여기서도 try로 보호한다.
try:
    from src.app.services.llm.engines.openai_engine import OpenAIEngine  # lazy import inside engine
except Exception:
    OpenAIEngine = None  # type: ignore


@dataclass
class EngineRegistry:
    engines: Dict[str, LLMEngine] = field(default_factory=dict)

    def register(self, engine: LLMEngine) -> None:
        self.engines[engine.provider_name()] = engine

    def get(self, provider: str) -> Optional[LLMEngine]:
        return self.engines.get(provider)


_DEFAULT_REGISTRY: Optional[EngineRegistry] = None


def build_default_registry() -> EngineRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is not None:
        return _DEFAULT_REGISTRY

    reg = EngineRegistry()

    # Always available dummy engines
    reg.register(DummyOpenAIEngine())
    reg.register(DummyGeminiEngine())

    # Real OpenAI engine (if class import succeeded)
    if OpenAIEngine is not None:
        reg.register(OpenAIEngine())

    # Aliases (very important)
    # - "openai" should exist (either real OpenAIEngine or dummy_openai)
    # - "gemini" should exist (dummy_gemini for now)
    if "openai" not in reg.engines and "dummy_openai" in reg.engines:
        reg.engines["openai"] = reg.engines["dummy_openai"]

    if "gemini" not in reg.engines and "dummy_gemini" in reg.engines:
        reg.engines["gemini"] = reg.engines["dummy_gemini"]

    _DEFAULT_REGISTRY = reg
    return reg
