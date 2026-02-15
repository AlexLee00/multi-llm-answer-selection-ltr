# apps/api/src/app/routers/ask.py
from __future__ import annotations

import os
import hashlib
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.app.schemas import AskRequest, AskResponse
from src.app.dependencies import get_db
from src.app.db.models import UserAnon, Context, Question, Candidate, Selection
from src.app.services.generator import generate_dummy_candidates
from src.app.services.selector import rule_select
from src.app.services.ranker import ltr_choose_best

router = APIRouter()


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, db: Session = Depends(get_db)):
    served_policy_env = os.getenv("SERVED_POLICY", "rule").strip().lower()
    if served_policy_env not in ("rule", "ltr"):
        served_policy_env = "rule"

    # ✅ env 로드 확인
    print("[ASK] env SERVED_POLICY =", served_policy_env)

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

        # 4) Generate candidates
        dummy_candidates = generate_dummy_candidates(request.question)

        db_candidates: List[Candidate] = []
        for c in dummy_candidates:
            ans = c["answer_summary"]
            cand = Candidate(
                question_id=question.question_id,
                provider=c["provider"],
                model=c["model"],
                answer_hash=_sha256(ans),
                answer_summary=ans,
                feature_version="fv1",
                has_code=bool(c.get("has_code", False)),
                len_words=len(ans.split()),
                step_score=1 if "Step" in ans else 0,
                has_bullets=bool(c.get("has_bullets", False)),
                has_warning=bool(c.get("has_warning", False)),
            )
            db.add(cand)
            db.flush()  # cand.candidate_id 확보
            db_candidates.append(cand)

        if len(db_candidates) < 2:
            raise RuntimeError("Need at least 2 candidates for selection/pairwise feedback.")

        # 5) Rule choice
        selected_dict = rule_select(dummy_candidates)
        selected_hash = _sha256(selected_dict["answer_summary"])
        rule_choice = next(c for c in db_candidates if c.answer_hash == selected_hash)

        # 6) LTR choice: ✅ (choice, model_version, error) 형태로 받는다
        ltr_choice: Optional[Candidate] = None
        ltr_choice_id = None
        ltr_model_version: Optional[str] = None
        ltr_error: Optional[str] = None

        if served_policy_env == "ltr":
            try:
                print("[ASK][LTR] try ltr_choose_best(db, candidates) ...")

                # ✅ ranker가 아래 튜플을 반환하도록 맞춘다:
                # (best_candidate | None, model_version | None, error_message | None)
                ltr_choice, ltr_model_version, ltr_error = ltr_choose_best(db, db_candidates)

                if ltr_choice is not None:
                    ltr_choice_id = ltr_choice.candidate_id
                    print(
                        "[ASK][LTR] success, ltr_choice_id =",
                        str(ltr_choice_id),
                        "| model_version =",
                        ltr_model_version,
                    )
                else:
                    print("[ASK][LTR] None (no model or no decision) | err =", ltr_error)

            except Exception as e:
                ltr_error = repr(e)
                print("[ASK][LTR_FALLBACK]", ltr_error)
                ltr_choice = None
                ltr_choice_id = None
                ltr_model_version = None

        # 7) Decide served choice
        if served_policy_env == "ltr" and ltr_choice is not None:
            served_choice = ltr_choice
            served_policy = "ltr"
            served_model_version = ltr_model_version  # ✅ LTR served면 기록
        else:
            served_choice = rule_choice
            served_policy = "rule"
            served_model_version = None  # ✅ rule served면 model_version 비움

        print(
            "[ASK] served_policy =", served_policy,
            "| rule_choice =", str(rule_choice.candidate_id),
            "| ltr_choice =", (str(ltr_choice_id) if ltr_choice_id else None),
            "| model_version =", served_model_version,
            "| ltr_error =", ltr_error,
        )

        # 8) Selection row (✅ model_version 저장)
        selection = Selection(
            question_id=question.question_id,
            rule_choice_candidate_id=rule_choice.candidate_id,
            ltr_choice_candidate_id=ltr_choice_id,
            served_choice_candidate_id=served_choice.candidate_id,
            served_policy=served_policy,
            model_version=served_model_version,  # ✅ 핵심!
            feature_version="fv1",
        )
        db.add(selection)

        # 9) Commit once
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
