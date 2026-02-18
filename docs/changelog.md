# Changelog

---

## [현재] 버그 수정 세션

### Fixed

- **`dependencies.py` — `load_dotenv()` CWD 의존 문제**
  - `load_dotenv()` → `find_dotenv()` + `load_dotenv(dotenv_path=...)` 로 변경
  - 어느 디렉터리에서 `uvicorn`을 실행해도 `.env`를 올바르게 탐색
  - `DB_URL` 누락 시 명확한 `RuntimeError` 발생 (탐색 경로 포함)
  - 중복 import (`Base`, `models`) 및 미사용 import (`Path`) 정리

- **`dummy_openai.py` — `request.user_prompt` AttributeError**
  - `EngineRequest` 데이터클래스에 `user_prompt` 필드 없음
  - `request.user_prompt` → `(request.params_json or {}).get("_user_prompt", "")` 로 수정
  - 프롬프트는 `generator.py`에서 `params_json["_user_prompt"]`에 주입됨

- **`dummy_gemini.py` — `request.user_prompt` AttributeError**
  - 동일 버그, 동일 수정

- **`ask.py` — `r.answer_summary` AttributeError**
  - `generate_candidates_v1()`의 반환값은 `List[Dict]`인데 속성(dot notation)으로 접근
  - `r.answer_summary` → `r.get("answer_summary")`
  - `r.provider`, `r.model` → `r["provider"]`, `r["model"]`

### Infrastructure

- **PostgreSQL 컨테이너 미실행 → 500 `Connection refused`**
  - 서버 실행 전 `docker compose -f infra/docker-compose.yml up -d` 필수
  - 올바른 실행 순서: PostgreSQL 컨테이너 → `uvicorn` API 서버

---

## [이전] 초기 프로토타입

### Added

- `/ask` 응답에 pairwise feedback용 편의 필드 추가
  - `question_id`, `candidate_a_id`, `candidate_b_id`, `served_choice_candidate_id`
- `v_pairwise_train` 뷰: 학습 데이터 추출용
- ML 파이프라인 스크립트
  - `scripts/make_snapshot.py`
  - `scripts/export_trainset.py`
  - `scripts/train_baseline.py`
  - `scripts/register_model.py`
- LTR ranker 서비스 (`ranker.py`)
  - 프로세스 메모리 모델 캐시
  - DB 최신 버전 자동 조회
  - pairwise tournament 방식 선택
- LLM 파이프라인 패키지 (`services/llm/`)
  - `EngineRequest` / `EngineResult` 데이터클래스 (`types.py`)
  - `LLMEngine` ABC (`base.py`)
  - `build_prompts_v1()` 프롬프트 빌더 (`prompt_builder.py`)
  - `EngineRegistry` + `build_default_registry()` 싱글턴 (`registry.py`)
  - `run_sequential()` 오케스트레이터 (`orchestrator.py`)
  - `OpenAIEngine` (실제 API), `DummyOpenAIEngine`, `DummyGeminiEngine`

### Changed

- `schemas.py`: Enum 기반 Pydantic 검증 (Swagger dropdown)
- `/feedback` 요청 필드: DB 컬럼명 일치
  - `candidate_a_id`, `candidate_b_id`, `user_choice`, `reason_tags`, `note`
- `/ask` 트랜잭션: `flush()` + 단일 `commit()` 구조
- `selections` 테이블: `model_version` 컬럼 추가 (LTR 서빙 시 기록)
- `ask.py`: feature 추출 함수 인라인화
  - `_has_code()`, `_has_bullets()`, `_has_warning()`

### Environment

| 변수 | 설명 |
|---|---|
| `SERVED_POLICY` | `rule` \| `ltr` |
| `ACTIVE_MODEL_VERSION` | 모델 버전 고정 (선택) |
| `DB_URL` | PostgreSQL 연결 문자열 (필수) |
| `OPENAI_API_KEY` | OpenAI API Key |
| `USE_DUMMY_GEMINI` | `1` 설정 시 Gemini 더미 사용 |

### Known Issues / Notes

- 학습 데이터가 단일 클래스인 경우 → `DummyClassifier` fallback
- 소량 데이터에서는 accuracy 불안정 → 충분한 pairwise feedback 수집 필요
