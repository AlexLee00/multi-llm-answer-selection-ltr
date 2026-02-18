# Architecture

## 1. 전체 요청 흐름

```
Client
 └─ POST /api/v1/ask
     ├─ 1) UserAnon 저장 (role, level)
     ├─ 2) Context 저장 (role, level, goal, stack, constraints)
     ├─ 3) Question 저장 (user_id, context_id, domain, question_text_hash)
     ├─ 4) LLM Candidate 생성
     │     generator.py → generate_candidates_v1()
     │       ├─ _mk_req() 로 EngineRequest 2개 구성 (openai, gemini)
     │       ├─ build_prompts_v1() 로 system/user 프롬프트 생성
     │       │     → params_json["_system_prompt"], ["_user_prompt"] 에 주입
     │       └─ run_sequential(registry, reqs) 로 순차 실행
     │             ├─ OpenAIEngine.generate() → 실제 API 호출
     │             │   (OPENAI_API_KEY 없으면 error 반환)
     │             ├─ DummyOpenAIEngine.generate() → params_json["_user_prompt"] 사용
     │             └─ DummyGeminiEngine.generate() → params_json["_user_prompt"] 사용
     ├─ 5) Feature 추출 (ask.py 인라인)
     │     has_code: ``` 포함 여부
     │     has_bullets: \n- / \n* / \n• 포함 여부
     │     has_warning: "warning" / "주의" 포함 여부
     │     step_score: "Step" / "단계" 포함 여부
     │     len_words: 공백 분리 단어 수
     ├─ 6) Candidate DB 저장 (feature_version="fv1")
     ├─ 7) Rule 선택
     │     selector.rule_select(selector_inputs)
     │     → len>50 +1, has_code +2, "Step" +1
     ├─ 8) LTR 선택 (SERVED_POLICY=ltr 시)
     │     ranker.ltr_choose_best(db, db_candidates)
     │     → ACTIVE_MODEL_VERSION 또는 DB 최신 모델 로드
     │     → 후보 간 pairwise tournament scoring
     │     → 오류 시 (None, mv, error_msg) 반환
     ├─ 9) served_choice 결정
     │     ltr 성공 → ltr_choice 서빙 (served_policy="ltr")
     │     그 외   → rule_choice 서빙 (served_policy="rule")
     ├─ 10) Selection 저장
     │      rule_choice_candidate_id
     │      ltr_choice_candidate_id
     │      served_choice_candidate_id
     │      served_policy, model_version, feature_version
     └─ 11) 응답 반환
            question_id, selected_candidate_id, selected_answer_summary
            candidate_a_id, candidate_b_id, served_choice_candidate_id

Client
 └─ POST /api/v1/feedback
     └─ feedback_pairwise 저장
           question_id, candidate_a_id, candidate_b_id
           user_choice (a/b/tie/bad), reason_tags, note

Batch ML Pipeline
 └─ make_snapshot → export_trainset → train_baseline → register_model
```

---

## 2. 모듈 구조

```
src/app/
  main.py               FastAPI app 생성, CORS 미들웨어, 라우터 등록
                        prefix: /api/v1
  dependencies.py       DB 세션 의존성
                        find_dotenv()로 .env 탐색 (CWD 무관)
                        DB_URL 누락 시 RuntimeError
  schemas.py            Pydantic 요청/응답 모델
                        AskRequest, AskResponse, FeedbackRequest, FeedbackResponse
  db/models.py          SQLAlchemy ORM
                        UserAnon, Context, Question, Candidate,
                        Selection, FeedbackPairwise, Snapshot, ModelRegistry

  routers/
    ask.py              POST /api/v1/ask
    feedback.py         POST /api/v1/feedback

  services/
    generator.py        generate_candidates_v1()
                        EngineRequest 구성 → 프롬프트 주입 → run_sequential
    selector.py         rule_select(candidates: List[dict]) → dict
    ranker.py           ltr_choose_best(db, candidates) → (Candidate|None, str|None, str|None)
                        프로세스 메모리 모델 캐시
    ltr_selector.py     pick_winner_with_model(model_path, a, b) → "a"|"b"
    model_registry.py   모델 등록 유틸

    llm/
      types.py          EngineRequest (dataclass), EngineResult (dataclass)
      base.py           LLMEngine (ABC)
      prompt_builder.py build_prompts_v1(req) → (system_str, user_str)
                        params_json["_question"]을 user 프롬프트로 변환
      registry.py       EngineRegistry
                        build_default_registry() → 싱글턴
                        OpenAIEngine > DummyOpenAIEngine 우선순위
      orchestrator.py   run_sequential(registry, reqs) → List[EngineResult]
      engines/
        openai_engine.py  OpenAIEngine: 실제 API 호출
                          OPENAI_API_KEY 없으면 error EngineResult 반환
                          system/user 프롬프트: params_json["_system_prompt"], ["_user_prompt"]
        dummy_openai.py   DummyOpenAIEngine: params_json["_user_prompt"] 사용
        dummy_gemini.py   DummyGeminiEngine: params_json["_user_prompt"] 사용
```

---

## 3. LLM 엔진 우선순위

```
build_default_registry()
  1. DummyOpenAIEngine 등록  (provider_name="openai")
  2. DummyGeminiEngine 등록  (provider_name="gemini")
  3. OpenAIEngine 등록       (provider_name="openai") ← 덮어씀
     → openai 패키지 import 실패 시 skip

결과: "openai" 키에 OpenAIEngine (실제), "gemini" 키에 DummyGeminiEngine
```

---

## 4. 프롬프트 흐름

```
generator._mk_req()
  → EngineRequest.params_json["_question"] = question

generator.generate_candidates_v1()
  → build_prompts_v1(req) 호출
  → req.params_json["_system_prompt"] = system
  → req.params_json["_user_prompt"]   = user

engine.generate(req)
  → params_json["_user_prompt"] 로 답변 생성
```

---

## 5. DB 주요 테이블 관계

```
users_anon ──┐
             ├─ questions ──┬─ candidates ──┬─ selections
contexts  ───┘              │               │
                            │               └─ feedback_pairwise
                            └─ selections

snapshots ── models
```

---

## 6. Rule vs LTR 비교 구조

```
Rule (selector.py)
  입력: List[dict]  (answer_summary, has_code 포함)
  로직: score = len>50(+1) + has_code(+2) + "Step"포함(+1)
  출력: 가장 높은 score의 dict

LTR (ranker.py)
  입력: List[Candidate] (DB ORM 객체)
  로직: 후보쌍 fv1 diff → predict_proba → tournament 평균
  출력: (best_Candidate | None, model_version | None, error | None)

selections 테이블
  → rule_choice_candidate_id  : Rule이 선택한 후보
  → ltr_choice_candidate_id   : LTR이 선택한 후보 (없으면 NULL)
  → served_choice_candidate_id: 실제 사용자에게 제공된 후보
  → served_policy             : "rule" | "ltr"
```
