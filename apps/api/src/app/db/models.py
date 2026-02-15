from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


ROLE_ENUM = Enum("planner", "designer", "dev", "tester", "other", name="role_enum")
LEVEL_ENUM = Enum("beginner", "intermediate", "advanced", name="level_enum")
GOAL_ENUM = Enum("concept", "practice", "assignment", "interview", "other", name="goal_enum")
QTYPE_ENUM = Enum("controlled", "free", name="question_type_enum")
CHOICE_ENUM = Enum("a", "b", "tie", "bad", name="pairwise_choice_enum")
POLICY_ENUM = Enum("single_llm_openai", "single_llm_gemini", "rule", "ltr", name="served_policy_enum")


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now():
    # DB 서버 시간이 single source of truth가 되도록 server_default(func.now())를 사용한다.
    # 이 함수는 혹시라도 python-side default가 필요해질 때를 대비한 placeholder.
    return datetime.utcnow()


class UserAnon(Base):
    __tablename__ = "users_anon"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    role: Mapped[str] = mapped_column(ROLE_ENUM, nullable=False)
    level: Mapped[str] = mapped_column(LEVEL_ENUM, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Context(Base):
    __tablename__ = "contexts"

    context_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    role: Mapped[str] = mapped_column(ROLE_ENUM, nullable=False)
    level: Mapped[str] = mapped_column(LEVEL_ENUM, nullable=False)
    goal: Mapped[str] = mapped_column(GOAL_ENUM, nullable=False)

    stack: Mapped[str | None] = mapped_column(String(200), nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Question(Base):
    __tablename__ = "questions"

    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users_anon.user_id"), nullable=False)
    context_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contexts.context_id"), nullable=False)

    question_type: Mapped[str] = mapped_column(QTYPE_ENUM, nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)

    question_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.question_id"), nullable=False)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)

    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)

    params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    answer_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    answer_summary: Mapped[str] = mapped_column(Text, nullable=False)

    feature_version: Mapped[str] = mapped_column(String(20), nullable=False, default="fv1")

    # extracted features (v1)
    len_words: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_code: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    step_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # v1 simplicity
    has_bullets: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Selection(Base):
    __tablename__ = "selections"

    selection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.question_id"), nullable=False)

    rule_choice_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.candidate_id"), nullable=True
    )
    ltr_choice_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.candidate_id"), nullable=True
    )
    served_choice_candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.candidate_id"), nullable=False
    )

    served_policy: Mapped[str] = mapped_column(POLICY_ENUM, nullable=False)

    model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    feature_version: Mapped[str] = mapped_column(String(20), nullable=False, default="fv1")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class FeedbackPairwise(Base):
    __tablename__ = "feedback_pairwise"

    feedback_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.question_id"), nullable=False)

    candidate_a_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.candidate_id"), nullable=False)
    candidate_b_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.candidate_id"), nullable=False)

    user_choice: Mapped[str] = mapped_column(CHOICE_ENUM, nullable=False)
    reason_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(30)), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Snapshot(Base):
    __tablename__ = "snapshots"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    data_range_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ModelRegistry(Base):
    __tablename__ = "models"

    model_version: Mapped[str] = mapped_column(String(40), primary_key=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("snapshots.snapshot_id"), nullable=False)

    feature_version: Mapped[str] = mapped_column(String(20), nullable=False)

    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(255), nullable=False)

    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
