from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import hashlib

from src.app.schemas import AskRequest, AskResponse
from src.app.dependencies import get_db
from src.app.db.models import UserAnon, Context, Question, Candidate, Selection
from src.app.services.generator import generate_dummy_candidates
from src.app.services.selector import rule_select

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, db: Session = Depends(get_db)):
    try:
        # 1️⃣ User 생성
        user = UserAnon(role=request.user.role, level=request.user.level)
        db.add(user)
        db.flush()  # PK 확보

        # 2️⃣ Context 생성
        context = Context(
            role=request.user.role,
            level=request.user.level,
            goal=request.context.goal,
            stack=request.context.stack,
            constraints=request.context.constraints,
        )
        db.add(context)
        db.flush()

        # 3️⃣ Question 생성
        question_hash = hashlib.sha256(request.question.encode("utf-8")).hexdigest()
        question = Question(
            user_id=user.user_id,
            context_id=context.context_id,
            question_type="free",
            domain=request.domain,
            question_text_hash=question_hash,
        )
        db.add(question)
        db.flush()

        # 4️⃣ 후보 생성
        dummy_candidates = generate_dummy_candidates(request.question)

        db_candidates = []
        for c in dummy_candidates:
            answer_hash = hashlib.sha256(c["answer_summary"].encode("utf-8")).hexdigest()

            candidate = Candidate(
                question_id=question.question_id,
                provider=c["provider"],
                model=c["model"],
                answer_hash=answer_hash,
                answer_summary=c["answer_summary"],
                feature_version="v1",
                has_code=bool(c.get("has_code", False)),
                len_words=len(c["answer_summary"].split()),
                step_score=1 if "Step" in c["answer_summary"] else 0,
                has_bullets=False,
                has_warning=False,
            )
            db.add(candidate)
            db.flush()
            db_candidates.append(candidate)

        # 5️⃣ rule 선택
        selected_dict = rule_select(dummy_candidates)
        selected_hash = hashlib.sha256(selected_dict["answer_summary"].encode("utf-8")).hexdigest()
        selected_db = next(c for c in db_candidates if c.answer_hash == selected_hash)

        # 6️⃣ selection 저장
        selection = Selection(
            question_id=question.question_id,
            served_choice_candidate_id=selected_db.candidate_id,
            served_policy="rule",
        )
        db.add(selection)

        # 🔥 마지막에 한 번만 commit
        db.commit()

        return AskResponse(
            question_id=question.question_id,
            selected_candidate_id=selected_db.candidate_id,
            selected_answer_summary=selected_db.answer_summary,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
