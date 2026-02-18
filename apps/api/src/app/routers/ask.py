# apps/api/src/app/routers/ask.py
from __future__ import annotations

import os
import hashlib
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.app.schemas import AskRequest, AskResponse
from src.app.dependencies import get_db
from src.app.db.models import UserAnon, Context, Question, Candidate, Selection
from src.app.services.generator import generate_candidates_v1
from src.app.services.selector import rule_select
from src.app.services.ranker import ltr_choose_best

router = APIRouter()


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _has_code(text: str) -> bool:
    return "```" in (text or "")


def _has_bullets(text: str) -> bool:
    t = (text or "")
    return ("\n-" in t) or ("\n*" in t) or ("\n•" in t)


def _has_warning(text: str) -> bool:
    t = (text or "").lower()
    return ("warning" in t) or ("주의" in t) or ("주의사항" in t)


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, db: Session = Depends(get_db)):
    served_policy_env = os.getenv("SERVED_POLICY", "rule").strip().lower()
    if served_policy_env not in ("rule", "ltr"):
        served_policy_env = "rule"

    try:
        # 1) User
        user = UserAnon(role=request.user.role, level=request.user.level)
        db.add(user)
        db.flush()

        # 2) Context
        context = Context(
            role=request.user.role,
            level=request.user.level,
            goal=request.context.goal,
            stack=request.context.stack,
            constraints=request.context.constraints,
        )
        db.add(context)
        db.flush()

        # 3) Question
        question = Question(
            user_id=user.user_id,
            context_id=context.context_id,
            question_type="free",
            domain=request.domain,
            question_text_hash=_sha256(request.question),
        )
        db.add(question)
        db.flush()

        # 4) Generate candidates (LLM pipeline)
        results = generate_candidates_v1(
            question=request.question,
            role=request.user.role,
            level=request.user.level,
            goal=request.context.goal,
            stack=request.context.stack,
            constraints=request.context.constraints,
            domain=request.domain,
        )

        # 5) Persist candidates
        db_candidates: List[Candidate] = []
        for r in results:
            ans = (r.get("answer_summary") or "").strip()

            cand = Candidate(
                question_id=question.question_id,
                provider=r["provider"],
                model=r["model"],
                answer_hash=_sha256(ans),
                answer_summary=ans,
                feature_version="fv1",
                has_code=_has_code(ans),
                len_words=len(ans.split()),
                step_score=1 if ("Step" in ans or "단계" in ans) else 0,
                has_bullets=_has_bullets(ans),
                has_warning=_has_warning(ans),
            )
            db.add(cand)
            db.flush()
            db_candidates.append(cand)

        if len(db_candidates) < 2:
            raise RuntimeError("Need at least 2 candidates for selection/pairwise feedback.")

        # 6) Rule choice (selector는 dict list를 기대 -> 변환)
        selector_inputs = [
            {
                "provider": c.provider,
                "model": c.model,
                "answer_summary": c.answer_summary,
                "has_code": bool(c.has_code),
            }
            for c in db_candidates
        ]
        selected_dict = rule_select(selector_inputs)
        selected_hash = _sha256(selected_dict["answer_summary"])
        rule_choice = next(c for c in db_candidates if c.answer_hash == selected_hash)

        # 7) LTR choice
        ltr_choice: Optional[Candidate] = None
        ltr_choice_id = None
        ltr_model_version: Optional[str] = None
        ltr_error: Optional[str] = None

        if served_policy_env == "ltr":
            ltr_choice, ltr_model_version, ltr_error = ltr_choose_best(db, db_candidates)
            if ltr_choice is not None:
                ltr_choice_id = ltr_choice.candidate_id

        # 8) Decide served choice
        if served_policy_env == "ltr" and ltr_choice is not None:
            served_choice = ltr_choice
            served_policy = "ltr"
            served_model_version = ltr_model_version
        else:
            served_choice = rule_choice
            served_policy = "rule"
            served_model_version = None

        # 9) Selection row
        selection = Selection(
            question_id=question.question_id,
            rule_choice_candidate_id=rule_choice.candidate_id,
            ltr_choice_candidate_id=ltr_choice_id,
            served_choice_candidate_id=served_choice.candidate_id,
            served_policy=served_policy,
            model_version=served_model_version,
            feature_version="fv1",
        )
        db.add(selection)

        db.commit()

        # Pairwise convenience ids: first two candidates (A,B)
        candidate_a_id = db_candidates[0].candidate_id
        candidate_b_id = db_candidates[1].candidate_id

        return AskResponse(
            question_id=question.question_id,
            selected_candidate_id=served_choice.candidate_id,
            selected_answer_summary=served_choice.answer_summary,
            candidate_a_id=candidate_a_id,
            candidate_b_id=candidate_b_id,
            served_choice_candidate_id=served_choice.candidate_id,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
