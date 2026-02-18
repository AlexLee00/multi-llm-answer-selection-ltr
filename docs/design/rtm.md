# Requirements Traceability Matrix (RTM)

---

## 기능 요구사항

| ID | 요구사항 | 구현 위치 | 상태 |
|---|---|---|---|
| FR-01 | 사용자 역할/숙련도 입력 수집 | `schemas.AskUser`, `db/models.UserAnon` | ✅ |
| FR-02 | 학습 맥락(goal/stack/constraints) 입력 수집 | `schemas.AskContext`, `db/models.Context` | ✅ |
| FR-03 | 사용자 질문 수신 및 저장 | `routers/ask.py`, `db/models.Question` | ✅ |
| FR-04 | 복수 LLM 후보 답변 생성 | `services/generator.generate_candidates_v1()` | ✅ |
| FR-05 | 프롬프트 빌더 (역할/맥락 반영) | `services/llm/prompt_builder.build_prompts_v1()` | ✅ |
| FR-06 | OpenAI 엔진 연동 | `services/llm/engines/openai_engine.OpenAIEngine` | ✅ |
| FR-07 | Gemini 더미 엔진 | `services/llm/engines/dummy_gemini.DummyGeminiEngine` | ✅ |
| FR-08 | 답변 feature 추출 (fv1) | `routers/ask.py` (`_has_code`, `_has_bullets` 등) | ✅ |
| FR-09 | Rule 기반 후보 선택 | `services/selector.rule_select()` | ✅ |
| FR-10 | LTR 기반 후보 선택 | `services/ranker.ltr_choose_best()` | ✅ |
| FR-11 | 서빙 정책 전환 (rule/ltr) | `.env SERVED_POLICY`, `routers/ask.py` | ✅ |
| FR-12 | Selection 저장 (rule/ltr/served 기록) | `db/models.Selection`, `routers/ask.py` | ✅ |
| FR-13 | Pairwise 피드백 수집 | `routers/feedback.py`, `db/models.FeedbackPairwise` | ✅ |
| FR-14 | 학습 데이터 스냅샷 생성 | `scripts/make_snapshot.py` | ✅ |
| FR-15 | 학습 데이터셋 추출 (CSV/JSONL) | `scripts/export_trainset.py` | ✅ |
| FR-16 | LTR 모델 학습 (LogisticRegression) | `scripts/train_baseline.py` | ✅ |
| FR-17 | 모델 레지스트리 등록 | `scripts/register_model.py`, `db/models.ModelRegistry` | ✅ |
| FR-18 | LTR 모델 자동 로드 및 캐시 | `services/ranker.py` (`_MODEL_CACHE`) | ✅ |
| FR-19 | 모델 버전 고정 지원 | `.env ACTIVE_MODEL_VERSION` | ✅ |

---

## 비기능 요구사항

| ID | 요구사항 | 구현 위치 | 상태 |
|---|---|---|---|
| NFR-01 | 환경변수 기반 설정 분리 | `apps/api/.env`, `dependencies.py` | ✅ |
| NFR-02 | .env 파일 경로 독립적 로드 | `dependencies.py` (`find_dotenv()`) | ✅ |
| NFR-03 | DB 연결 누락 시 명확한 오류 | `dependencies.py` (`RuntimeError`) | ✅ |
| NFR-04 | 트랜잭션 원자성 (flush + 단일 commit) | `routers/ask.py`, `routers/feedback.py` | ✅ |
| NFR-05 | LLM 엔진 오류 격리 (에러 EngineResult 반환) | `services/llm/engines/*.py` | ✅ |
| NFR-06 | LTR 모델 로드 실패 시 Rule fallback | `routers/ask.py` | ✅ |
| NFR-07 | 단일 클래스 학습 데이터 방어 | `scripts/train_baseline.py` (DummyClassifier) | ✅ |
| NFR-08 | CORS 허용 (로컬 개발) | `main.py` (CORSMiddleware) | ✅ |
| NFR-09 | Swagger UI 제공 | FastAPI 자동 생성 (`/docs`) | ✅ |
| NFR-10 | Pydantic Enum 검증 (Swagger dropdown) | `schemas.py` | ✅ |

---

## 연구 요구사항

| ID | 요구사항 | 구현 위치 | 상태 |
|---|---|---|---|
| RR-01 | Rule vs LTR 비교 가능 구조 | `selections` 테이블 (rule/ltr/served 분리 저장) | ✅ |
| RR-02 | Feature version 관리 | `candidates.feature_version`, `selections.feature_version` | ✅ |
| RR-03 | Model version 추적 | `selections.model_version`, `models` 테이블 | ✅ |
| RR-04 | 통제 질문 유형 지원 | `question_type_enum` (`controlled` \| `free`) | ✅ |
| RR-05 | 피드백 이유 태그 수집 | `feedback_pairwise.reason_tags` (varchar array) | ✅ |
| RR-06 | pairwise 학습 뷰 제공 | `v_pairwise_train` (alembic migration) | ✅ |
| RR-07 | Feature v2 확장 가능 구조 | `feature_version` 컬럼 설계 | 🔜 계획 |
