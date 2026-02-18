# API Contract

Base URL: `http://localhost:8000`
API Prefix: `/api/v1`
Swagger UI: `http://localhost:8000/docs`

---

## GET /

서비스 메타 정보 반환.

**Response `200`**
```json
{
  "name": "Multi-LLM Answer Selection API",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/health",
  "api_prefix": "/api/v1"
}
```

---

## GET /health

헬스체크.

**Response `200`**
```json
{ "status": "ok" }
```

---

## POST /api/v1/ask

사용자 질문을 받아 LLM 후보를 생성하고, Rule/LTR 기반으로 최적 답변을 선택하여 반환.

### Request Body

```json
{
  "user": {
    "role": "dev",
    "level": "beginner"
  },
  "context": {
    "goal": "practice",
    "stack": "python, fastapi",
    "constraints": "windows, no admin rights"
  },
  "question": "FastAPI에서 SQLAlchemy 세션 관리 방법?",
  "domain": "backend"
}
```

| 필드 | 타입 | 필수 | 허용값 |
|---|---|---|---|
| `user.role` | enum | ✅ | `planner` \| `designer` \| `dev` \| `tester` \| `other` |
| `user.level` | enum | ✅ | `beginner` \| `intermediate` \| `advanced` |
| `context.goal` | enum | ✅ | `concept` \| `practice` \| `assignment` \| `interview` \| `other` |
| `context.stack` | string | 선택 | 사용 기술 스택 (예: `python, fastapi`) |
| `context.constraints` | string | 선택 | 제약 조건 (예: `windows, no admin rights`) |
| `question` | string | ✅ | 질문 텍스트 (1자 이상) |
| `domain` | string | ✅ | 도메인 레이블 (예: `backend`) |

### Response `200`

```json
{
  "question_id": "df21117b-b0db-41bb-b9f7-80bce2800e34",
  "selected_candidate_id": "51948e7f-471b-4dfc-9562-6f19ea49bc7b",
  "selected_answer_summary": "[OpenAI Dummy]\nStep 1: ...\nStep 2: Example explanation.",
  "candidate_a_id": "51948e7f-471b-4dfc-9562-6f19ea49bc7b",
  "candidate_b_id": "5a0b3b4a-1111-2222-3333-444444444444",
  "served_choice_candidate_id": "51948e7f-471b-4dfc-9562-6f19ea49bc7b"
}
```

| 필드 | 설명 |
|---|---|
| `question_id` | 저장된 질문 UUID (`/feedback` 입력용) |
| `selected_candidate_id` | 선택된 후보 UUID |
| `selected_answer_summary` | 선택된 답변 텍스트 |
| `candidate_a_id` | 첫 번째 후보 UUID (`/feedback` 입력용) |
| `candidate_b_id` | 두 번째 후보 UUID (`/feedback` 입력용) |
| `served_choice_candidate_id` | 실제 서빙된 후보 UUID |

### Response `500`

```json
{ "detail": "<error message>" }
```

### 내부 처리 순서

```
1. UserAnon 저장  (role, level)
2. Context 저장   (role, level, goal, stack, constraints)
3. Question 저장  (user_id, context_id, domain, question_text_hash)
4. generate_candidates_v1() → LLM 후보 2개 생성
   - build_prompts_v1()로 system/user 프롬프트 구성
   - run_sequential(): OpenAIEngine + DummyGeminiEngine 순차 실행
5. Feature 추출 (fv1) → Candidate 저장
6. rule_select()  → Rule 기반 선택
7. ltr_choose_best() → LTR 기반 선택 (SERVED_POLICY=ltr 시)
8. served_choice 결정 → Selection 저장
9. 응답 반환
```

---

## POST /api/v1/feedback

사용자의 pairwise 선호 피드백을 저장.

### Request Body

```json
{
  "question_id": "df21117b-b0db-41bb-b9f7-80bce2800e34",
  "candidate_a_id": "51948e7f-471b-4dfc-9562-6f19ea49bc7b",
  "candidate_b_id": "5a0b3b4a-1111-2222-3333-444444444444",
  "user_choice": "a",
  "reason_tags": ["clarity", "has_steps"],
  "note": "A가 더 단계적으로 설명함"
}
```

| 필드 | 타입 | 필수 | 허용값 |
|---|---|---|---|
| `question_id` | UUID | ✅ | `/ask` 응답의 `question_id` |
| `candidate_a_id` | UUID | ✅ | `/ask` 응답의 `candidate_a_id` |
| `candidate_b_id` | UUID | ✅ | `/ask` 응답의 `candidate_b_id` |
| `user_choice` | enum | ✅ | `a` \| `b` \| `tie` \| `bad` |
| `reason_tags` | string[] | 선택 | 선택 이유 태그 (예: `["clarity", "has_steps"]`) |
| `note` | string | 선택 | 자유 기술 메모 |

### Response `200`

```json
{ "feedback_id": "aabbccdd-eeff-..." }
```

### Response `500`

```json
{ "detail": "<error message>" }
```

---

## 환경변수와 동작

| `SERVED_POLICY` | 동작 |
|---|---|
| `rule` | Rule 선택 결과를 사용자에게 서빙 |
| `ltr` | LTR 선택 시도 → 모델 없음/실패 시 Rule fallback |
