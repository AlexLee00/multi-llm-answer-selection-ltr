# Data Schema

ORM: SQLAlchemy (Declarative), DB: PostgreSQL 16

---

## Enum Types

```sql
role_enum     : planner | designer | dev | tester | other
level_enum    : beginner | intermediate | advanced
goal_enum     : concept | practice | assignment | interview | other
question_type_enum : controlled | free
pairwise_choice_enum : a | b | tie | bad
served_policy_enum   : single_llm_openai | single_llm_gemini | rule | ltr
```

---

## 테이블 상세

### users_anon

익명 사용자 정보.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `user_id` | UUID PK | 자동 생성 |
| `role` | role_enum | 사용자 역할 |
| `level` | level_enum | 숙련도 |
| `created_at` | timestamptz | 서버 기본값 |

---

### contexts

질문의 학습 맥락.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `context_id` | UUID PK | 자동 생성 |
| `role` | role_enum | 사용자 역할 |
| `level` | level_enum | 숙련도 |
| `goal` | goal_enum | 학습 목표 |
| `stack` | varchar(200) | 기술 스택 (nullable) |
| `constraints` | text | 제약 조건 (nullable) |
| `created_at` | timestamptz | 서버 기본값 |

---

### questions

사용자 질문.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `question_id` | UUID PK | 자동 생성 |
| `user_id` | UUID FK → users_anon | |
| `context_id` | UUID FK → contexts | |
| `question_type` | question_type_enum | `controlled` \| `free` |
| `domain` | varchar(50) | 도메인 레이블 (예: backend) |
| `question_text_hash` | varchar(64) | SHA-256 해시 |
| `created_at` | timestamptz | 서버 기본값 |

---

### candidates

LLM이 생성한 후보 답변 및 추출된 feature.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `candidate_id` | UUID PK | 자동 생성 |
| `question_id` | UUID FK → questions | |
| `provider` | varchar(50) | `openai` \| `gemini` \| `fallback` |
| `model` | varchar(80) | 모델명 (예: `gpt-4o-mini`) |
| `latency_ms` | int | 생성 지연 시간 (ms) |
| `tokens_in` | int | 입력 토큰 수 (nullable) |
| `tokens_out` | int | 출력 토큰 수 (nullable) |
| `params_json` | jsonb | 생성 파라미터 (nullable) |
| `answer_hash` | varchar(64) | SHA-256 해시 |
| `answer_summary` | text | 답변 전문 |
| `feature_version` | varchar(20) | `fv1` |
| `len_words` | int | 단어 수 |
| `has_code` | bool | 코드블록 포함 여부 |
| `step_score` | int | 단계형 설명 여부 (0 또는 1) |
| `has_bullets` | bool | 불릿 포함 여부 |
| `has_warning` | bool | 경고 문구 포함 여부 |
| `created_at` | timestamptz | 서버 기본값 |

**Feature 추출 로직 (ask.py)**:

```python
has_code    = "```" in answer
has_bullets = "\n-" in answer or "\n*" in answer or "\n•" in answer
has_warning = "warning" in answer.lower() or "주의" in answer
step_score  = 1 if ("Step" in answer or "단계" in answer) else 0
len_words   = len(answer.split())
```

---

### selections

각 질문에 대해 Rule/LTR이 선택한 후보와 실제 서빙된 후보 기록.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `selection_id` | UUID PK | 자동 생성 |
| `question_id` | UUID FK → questions | |
| `rule_choice_candidate_id` | UUID FK → candidates | Rule이 선택한 후보 |
| `ltr_choice_candidate_id` | UUID FK → candidates | LTR이 선택한 후보 (nullable) |
| `served_choice_candidate_id` | UUID FK → candidates | 실제 서빙된 후보 |
| `served_policy` | served_policy_enum | `rule` \| `ltr` |
| `model_version` | varchar(40) | LTR 서빙 시 사용된 모델 버전 (nullable) |
| `feature_version` | varchar(20) | `fv1` |
| `created_at` | timestamptz | 서버 기본값 |

---

### feedback_pairwise

사용자 pairwise 선호 피드백.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `feedback_id` | UUID PK | 자동 생성 |
| `question_id` | UUID FK → questions | |
| `candidate_a_id` | UUID FK → candidates | 비교 대상 A |
| `candidate_b_id` | UUID FK → candidates | 비교 대상 B |
| `user_choice` | pairwise_choice_enum | `a` \| `b` \| `tie` \| `bad` |
| `reason_tags` | varchar(30)[] | 선택 이유 태그 배열 (nullable) |
| `note` | text | 자유 기술 메모 (nullable) |
| `created_at` | timestamptz | 서버 기본값 |

---

### snapshots

ML 학습용 데이터 스냅샷 메타데이터.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `snapshot_id` | UUID PK | 자동 생성 |
| `data_range_json` | jsonb | `{min_date, max_date, n_rows}` |
| `row_count` | int | 집계 행 수 |
| `created_at` | timestamptz | 서버 기본값 |

---

### models

학습된 LTR 모델 레지스트리.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `model_version` | varchar(40) PK | 버전 식별자 |
| `snapshot_id` | UUID FK → snapshots | 학습에 사용된 스냅샷 |
| `feature_version` | varchar(20) | `fv1` |
| `metrics_json` | jsonb | accuracy 등 성능 지표 |
| `artifact_path` | varchar(255) | `.pkl` 파일 경로 |
| `trained_at` | timestamptz | 서버 기본값 |

---

## 테이블 관계

```
users_anon ──┐
             ├──► questions ──┬──► candidates ◄──┬── selections
contexts  ───┘                │                  │
                              │                  └── feedback_pairwise
                              └──► selections

snapshots ──► models
```

---

## 학습 뷰

### v_pairwise_train

```sql
SELECT
    fp.feedback_id,
    fp.question_id,
    fp.candidate_a_id,
    fp.candidate_b_id,
    fp.user_choice,
    -- Candidate A features
    ca.len_words        AS a_len_words,
    ca.has_code         AS a_has_code,
    ca.step_score       AS a_step_score,
    ca.has_bullets      AS a_has_bullets,
    ca.has_warning      AS a_has_warning,
    -- Candidate B features
    cb.len_words        AS b_len_words,
    cb.has_code         AS b_has_code,
    cb.step_score       AS b_step_score,
    cb.has_bullets      AS b_has_bullets,
    cb.has_warning      AS b_has_warning
FROM feedback_pairwise fp
JOIN candidates ca ON ca.candidate_id = fp.candidate_a_id
JOIN candidates cb ON cb.candidate_id = fp.candidate_b_id
WHERE fp.user_choice IN ('a', 'b');
```
