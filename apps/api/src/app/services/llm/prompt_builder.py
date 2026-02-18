# apps/api/src/app/services/llm/prompt_builder.py
from __future__ import annotations

from typing import Tuple

from src.app.services.llm.types import EngineRequest


def build_prompts_v1(req: EngineRequest) -> Tuple[str, str]:
    system = (
        "You are a helpful assistant for IT learners.\n"
        f"Role: {req.role}\n"
        f"Level: {req.level}\n"
        f"Goal: {req.goal}\n"
        f"Stack: {req.stack}\n"
        f"Constraints: {req.constraints}\n"
        f"Domain: {req.domain}\n"
        "Answer clearly with step-by-step reasoning when appropriate."
    )

    user = f"Question:\n{req.params_json.get('_question','') if req.params_json else ''}".strip()
    return system, user


# alias for compatibility
def build_prompts(req: EngineRequest) -> Tuple[str, str]:
    return build_prompts_v1(req)
