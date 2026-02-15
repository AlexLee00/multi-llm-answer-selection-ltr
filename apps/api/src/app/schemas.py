from enum import Enum
from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class Role(str, Enum):
    planner = "planner"
    designer = "designer"
    dev = "dev"
    tester = "tester"
    other = "other"


class Level(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class UserInput(BaseModel):
    role: Role
    level: Level


class ContextInput(BaseModel):
    goal: str
    stack: Optional[str] = None
    constraints: Optional[str] = None


class AskRequest(BaseModel):
    user: UserInput
    context: ContextInput
    question: str
    domain: str


class AskResponse(BaseModel):
    question_id: UUID
    selected_candidate_id: UUID
    selected_answer_summary: str
