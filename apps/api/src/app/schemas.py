from __future__ import annotations

from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =========================
# Enums (must match DB enums)
# =========================

class RoleEnum(str, Enum):
    planner = "planner"
    designer = "designer"
    dev = "dev"
    tester = "tester"
    other = "other"


class LevelEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class GoalEnum(str, Enum):
    concept = "concept"
    practice = "practice"
    assignment = "assignment"
    interview = "interview"
    other = "other"


class PairwiseChoiceEnum(str, Enum):
    a = "a"
    b = "b"
    tie = "tie"
    bad = "bad"


# =========================
# /ask
# =========================

class AskUser(BaseModel):
    role: RoleEnum = Field(..., description="User role (enum).", examples=["planner"])
    level: LevelEnum = Field(..., description="User level (enum).", examples=["beginner"])


class AskContext(BaseModel):
    goal: GoalEnum = Field(..., description="Learning goal (enum).", examples=["practice"])
    stack: Optional[str] = Field(None, description="Tech stack or tools.", examples=["python, fastapi"])
    constraints: Optional[str] = Field(None, description="Constraints (device/time/policy).", examples=["windows, no admin rights"])


class AskRequest(BaseModel):
    user: AskUser
    context: AskContext
    question: str = Field(..., min_length=1, description="User question text.", examples=["FastAPI에서 SQLAlchemy 세션 관리 방법?"])
    domain: str = Field(..., min_length=1, description="Domain label for analysis/training.", examples=["backend"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": {"role": "planner", "level": "beginner"},
                    "context": {"goal": "practice", "stack": "python, fastapi", "constraints": "windows, no admin rights"},
                    "question": "FastAPI에서 SQLAlchemy 세션 관리 방법?",
                    "domain": "backend",
                }
            ]
        }
    }


class AskResponse(BaseModel):
    question_id: UUID
    selected_candidate_id: UUID
    selected_answer_summary: str

    # Pairwise testing convenience (copy/paste into /feedback)
    candidate_a_id: Optional[UUID] = Field(
        default=None,
        description="Candidate A id for pairwise feedback test (optional).",
    )
    candidate_b_id: Optional[UUID] = Field(
        default=None,
        description="Candidate B id for pairwise feedback test (optional).",
    )
    served_choice_candidate_id: Optional[UUID] = Field(
        default=None,
        description="Which candidate was served to user (optional).",
    )


# =========================
# /feedback
# =========================

class FeedbackRequest(BaseModel):
    question_id: UUID = Field(..., description="Question id from /ask response.")

    # Must match DB column names in feedback_pairwise
    candidate_a_id: UUID = Field(..., description="Candidate A id from /ask response.")
    candidate_b_id: UUID = Field(..., description="Candidate B id from /ask response.")

    user_choice: PairwiseChoiceEnum = Field(..., description="a/b/tie/bad")
    reason_tags: Optional[List[str]] = Field(
        default=None,
        description="Optional reason tags (lightweight labels).",
        examples=[["clarity", "correctness"]],
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional free-text note.",
        examples=["B가 더 구체적이고 단계가 명확함"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question_id": "df21117b-b0db-41bb-b9f7-80bce2800e34",
                    "candidate_a_id": "51948e7f-471b-4dfc-9562-6f19ea49bc7b",
                    "candidate_b_id": "5a0b3b4a-1111-2222-3333-444444444444",
                    "user_choice": "a",
                    "reason_tags": ["clarity", "has_steps"],
                    "note": "A가 더 단계적으로 설명함",
                }
            ]
        }
    }


class FeedbackResponse(BaseModel):
    feedback_id: UUID
