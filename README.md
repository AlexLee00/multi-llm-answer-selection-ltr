# multi-llm-answer-selection-ltr

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green.svg)
![Postgres](https://img.shields.io/badge/PostgreSQL-16-blue)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Research](https://img.shields.io/badge/Research-LTR-orange.svg)

Research platform for **Multi-LLM Answer Selection** using **Learning-to-Rank (LTR)**.

The system generates candidate answers from multiple LLM providers,
collects structured **pairwise human feedback**,
and trains a **ranker model** to improve answer selection quality for IT learners.

---

# 🎯 Research Objective

**Target Users**

* University students
* Roles: planner / designer / developer / tester
* Not necessarily professional developers

**Research Goal**

* Improve answer selection quality via LTR
* Measure performance improvement over rule-based baseline
* Produce KCI-level empirical evaluation

---

# 🔥 Core Idea

1. Generate candidate answers from multiple LLM providers (OpenAI + Gemini)
2. Extract lightweight features from answers (v1)
3. Select best answer via:
   * Rule baseline (heuristic scoring)
   * LTR model (pairwise logistic regression)
4. Collect structured pairwise feedback
5. Train batch ranking pipeline
6. Deploy latest model automatically for serving

---

# 🏗 Architecture (High-Level)

```
Client
 └─ POST /api/v1/ask
     ├─ UserAnon 저장
     ├─ Context 저장
     ├─ Question 저장
     ├─ LLM Candidate 생성 (OpenAI + Gemini, sequential)
     │   └─ prompt_builder → engine (real / dummy) → EngineResult
     ├─ Feature 추출 (fv1: len_words, has_code, step_score, has_bullets, has_warning)
     ├─ Candidate DB 저장
     ├─ Rule 선택 (selector.py)
     ├─ LTR 선택 (ranker.py, SERVED_POLICY=ltr 시)
     ├─ Selection 저장 (served_policy, model_version 기록)
     └─ 응답 반환

Client
 └─ POST /api/v1/feedback
     └─ feedback_pairwise 저장

Batch ML Pipeline
 └─ make_snapshot → export_trainset → train_baseline → register_model → LTR Serving
```

---

# 📂 Repository Structure

```
docs/
  architecture.md         # 전체 아키텍처
  changelog.md            # 변경 이력
  ml_pipeline.md          # ML 파이프라인 상세
  design/
    api-contract.md       # API 명세
    data-schema.md        # DB 스키마
    rtm.md                # Requirements Traceability Matrix
    threat-privacy.md     # 보안/개인정보 위협 분석
    controlled-questions.md  # 실험용 통제 질문셋
infra/
  docker-compose.yml      # PostgreSQL 16
apps/api/
  .env                    # 환경변수 (gitignore)
  alembic/                # DB 마이그레이션
  src/app/
    main.py               # FastAPI app, CORS, router 등록
    dependencies.py       # DB 세션 (find_dotenv 기반)
    schemas.py            # Pydantic 요청/응답 스키마
    db/models.py          # SQLAlchemy ORM 모델
    routers/
      ask.py              # POST /api/v1/ask
      feedback.py         # POST /api/v1/feedback
    services/
      generator.py        # generate_candidates_v1() - LLM 파이프라인 진입점
      selector.py         # rule_select() - 룰 기반 선택
      ranker.py           # ltr_choose_best() - LTR 선택
      ltr_selector.py     # pick_winner_with_model() - 모델 기반 단일 비교
      model_registry.py   # 모델 등록 유틸
      llm/
        types.py          # EngineRequest / EngineResult dataclass
        base.py           # LLMEngine ABC
        prompt_builder.py # build_prompts_v1() - system/user 프롬프트 생성
        registry.py       # EngineRegistry, build_default_registry()
        orchestrator.py   # run_sequential() - 엔진 순차 실행
        engines/
          openai_engine.py   # 실제 OpenAI API 호출
          dummy_openai.py    # OpenAI 더미 (테스트용)
          dummy_gemini.py    # Gemini 더미 (테스트용)
  scripts/
    make_snapshot.py
    export_trainset.py
    train_baseline.py
    register_model.py
artifacts/
  trainsets/              # 학습 데이터셋 (.csv / .jsonl)
  models/                 # 학습된 모델 (.pkl / .json)
```

---

# 🚀 Quick Start (Local)

## 1️⃣ 환경변수 설정

`apps/api/.env` 생성:

```env
DB_URL=postgresql+psycopg2://mlas:mlas_pw@127.0.0.1:5432/mlas

SERVED_POLICY=rule
# SERVED_POLICY=ltr  # LTR 모드 활성화 시

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_S=20

USE_DUMMY_GEMINI=1
GEMINI_MODEL=gemini-dummy

# ACTIVE_MODEL_VERSION=  # 특정 모델 버전 고정 시 (선택)
```

---

## 2️⃣ Start Postgres

```bash
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps
```

---

## 3️⃣ DB Migration

```bash
cd apps/api
alembic upgrade head
```

테이블 확인:

```bash
docker exec -it mlas_postgres psql -U mlas -d mlas -c "\dt"
```

Expected tables:

* users_anon
* contexts
* questions
* candidates
* selections
* feedback_pairwise
* snapshots
* models
* alembic_version

---

## 4️⃣ Run API

```bash
cd apps/api
uvicorn src.app.main:app --reload
```

Swagger UI:

```
http://localhost:8000/docs
```

---

# 🔁 End-to-End Flow

## Step 1 — Ask

`POST /api/v1/ask`

```json
{
  "user": { "role": "dev", "level": "beginner" },
  "context": { "goal": "practice", "stack": "python, fastapi", "constraints": "windows" },
  "question": "FastAPI에서 SQLAlchemy 세션 관리 방법?",
  "domain": "backend"
}
```

Response:

```json
{
  "question_id": "...",
  "selected_candidate_id": "...",
  "selected_answer_summary": "...",
  "candidate_a_id": "...",
  "candidate_b_id": "...",
  "served_choice_candidate_id": "..."
}
```

---

## Step 2 — Feedback

`POST /api/v1/feedback`

```json
{
  "question_id": "...",
  "candidate_a_id": "...",
  "candidate_b_id": "...",
  "user_choice": "a",
  "reason_tags": ["clarity"],
  "note": "A가 더 단계적으로 설명함"
}
```

---

# 🧠 ML Pipeline

## 1️⃣ Snapshot

```bash
python scripts/make_snapshot.py
```

## 2️⃣ Export Trainset

```bash
python scripts/export_trainset.py
```

출력: `artifacts/trainsets/<snapshot_id>.csv / .jsonl`

## 3️⃣ Train Model

```bash
python scripts/train_baseline.py
```

* Logistic Regression (pairwise diff features)
* 단일 클래스 시 DummyClassifier fallback
* 저장: `artifacts/models/<version>.pkl / .json`

## 4️⃣ Register Model

```bash
python scripts/register_model.py
```

`models` 테이블에 등록:
* model_version, snapshot_id, feature_version, metrics_json, artifact_path

---

# 🏁 LTR Serving Logic (`ranker.py`)

1. `ACTIVE_MODEL_VERSION` 환경변수 확인 → 없으면 DB에서 최신 버전 조회
2. 프로세스 메모리에 모델 캐시 (버전 변경 시 자동 갱신)
3. 후보쌍 pairwise diff feature 계산 (fv1: 5차원)
4. 토너먼트 방식 평균 win probability 계산
5. 최고 확률 후보 선택

`selections` 테이블 기록:
* `rule_choice_candidate_id`
* `ltr_choice_candidate_id`
* `served_choice_candidate_id`
* `served_policy` (`rule` | `ltr`)
* `model_version`

---

# 📊 Feature Design

## v1 (구현 완료)

| Feature | 추출 방법 |
|---|---|
| `len_words` | `len(answer.split())` |
| `has_code` | ` ``` ` 포함 여부 |
| `step_score` | "Step" / "단계" 포함 여부 |
| `has_bullets` | `\n-`, `\n*`, `\n•` 포함 여부 |
| `has_warning` | "warning" / "주의" 포함 여부 |

학습 입력: `diff = A_features - B_features` (5차원 벡터)

## v2 (계획)

* semantic similarity (question ↔ answer)
* embedding cosine distance
* hallucination risk indicators
* structural completeness score

---

# 🧪 Research Setup (Pilot)

* 참가자: 30명
* 인당 질문: ~10개

통제 질문 구성:
* Beginner ×2
* Intermediate ×2
* Advanced ×1
* 자유 질문

---

# 📈 Evaluation Metrics

* Rank Accuracy
* NDCG@1
* Rule baseline 대비 개선율
* Human preference agreement rate

---

# ⚙ Environment Variables

| 변수 | 필수 | 설명 |
|---|---|---|
| `DB_URL` | ✅ | PostgreSQL 연결 문자열 |
| `SERVED_POLICY` | ✅ | `rule` 또는 `ltr` |
| `OPENAI_API_KEY` | OpenAI 사용 시 | OpenAI API Key |
| `OPENAI_MODEL` | 선택 | 기본 `gpt-4o-mini` |
| `OPENAI_TIMEOUT_S` | 선택 | 기본 20초 |
| `USE_DUMMY_GEMINI` | 선택 | `1` 이면 Gemini 더미 사용 |
| `ACTIVE_MODEL_VERSION` | 선택 | LTR 모델 버전 고정 (없으면 최신) |

> `dependencies.py`는 `find_dotenv()`로 `.env`를 파일 위치 기준 상위 탐색하므로 어느 디렉터리에서 실행해도 안전합니다.

---

# ✅ Current Status

| 항목 | 상태 |
|---|---|
| DB 스키마 | ✅ 완료 |
| `/ask` 엔드포인트 | ✅ 완료 |
| `/feedback` 엔드포인트 | ✅ 완료 |
| LLM 파이프라인 (OpenAI + Gemini dummy) | ✅ 완료 |
| Rule 선택 | ✅ 완료 |
| LTR 선택 | ✅ 완료 |
| ML 파이프라인 (snapshot → train → register) | ✅ 완료 |
| Pairwise feedback 수집 | ✅ 완료 |
| Rule vs LTR 비교 가능 | ✅ 완료 |

---

# 🔜 Next Phase

1. Feature v2 확장 (semantic similarity 등)
2. 통제 실험 실행
3. 통계적 유의성 검증
4. 점진적 재학습 전략
5. 논문 구조화

---

# 📄 Design Documentation

```
docs/design/
  api-contract.md         # API 요청/응답 명세
  data-schema.md          # DB 테이블 스키마
  rtm.md                  # Requirements Traceability Matrix
  threat-privacy.md       # 보안/개인정보 위협 분석
  controlled-questions.md # 실험용 통제 질문셋
```

---

# 📜 License

MIT
