# apps/api/src/app/services/llm/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from .types import EngineRequest, EngineResult


class LLMEngine(ABC):

    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def generate(self, request: EngineRequest) -> EngineResult:
        pass
