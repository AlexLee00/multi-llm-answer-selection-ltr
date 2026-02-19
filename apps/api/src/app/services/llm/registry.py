# apps/api/src/app/services/llm/registry.py
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from src.app.services.llm.base import LLMEngine
from src.app.services.llm.engines.dummy_openai import DummyOpenAIEngine
from src.app.services.llm.engines.dummy_gemini import DummyGeminiEngine

# 실제 엔진은 import 실패해도 서버가 떠야 하므로 try로 보호한다.
try:
    from src.app.services.llm.engines.openai_engine import OpenAIEngine
except Exception:
    OpenAIEngine = None  # type: ignore

try:
    from src.app.services.llm.engines.gemini_engine import GeminiEngine
except Exception:
    GeminiEngine = None  # type: ignore


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

    # --- OpenAI ---
    # dummy를 먼저 등록한 뒤, 실제 엔진으로 덮어쓴다.
    reg.register(DummyOpenAIEngine())
    if OpenAIEngine is not None:
        reg.register(OpenAIEngine())  # provider_name="openai" 로 덮어씀

    # --- Gemini ---
    # USE_DUMMY_GEMINI=1 이면 dummy 유지, 아니면 실제 GeminiEngine으로 덮어쓴다.
    reg.register(DummyGeminiEngine())
    use_dummy = os.getenv("USE_DUMMY_GEMINI", "0").strip() == "1"
    if not use_dummy and GeminiEngine is not None:
        reg.register(GeminiEngine())  # provider_name="gemini" 로 덮어씀

    _DEFAULT_REGISTRY = reg
    return reg
