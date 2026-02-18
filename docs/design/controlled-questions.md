# Controlled Questions

연구 실험의 재현성과 수준별 비교를 위해 사전 정의된 통제 질문셋.

`question_type = "controlled"` 로 저장.

---

## 구성 원칙

- 역할(role): `dev` 고정 (파일럿 v1)
- 도메인(domain): `backend` / `frontend` / `algorithm`
- 수준별 2세트 × 3수준 = 6문항 + 자유 질문

---

## Beginner (level = beginner)

### BQ-01
```
question : Python에서 리스트와 딕셔너리의 차이점은 무엇인가요?
domain   : python_basic
goal     : concept
stack    : python
```

### BQ-02
```
question : FastAPI에서 경로 매개변수(path parameter)를 어떻게 사용하나요?
domain   : backend
goal     : practice
stack    : python, fastapi
```

---

## Intermediate (level = intermediate)

### IQ-01
```
question : SQLAlchemy에서 세션(Session)과 연결(Connection)의 차이를 설명하고,
           FastAPI에서 세션을 올바르게 관리하는 방법을 알려주세요.
domain   : backend
goal     : practice
stack    : python, fastapi, sqlalchemy
```

### IQ-02
```
question : REST API 설계 시 PUT과 PATCH의 차이점과 각각 언제 사용해야 하는지
           예시 코드와 함께 설명해주세요.
domain   : backend
goal     : concept
stack    : python, fastapi
```

---

## Advanced (level = advanced)

### AQ-01
```
question : PostgreSQL에서 인덱스 종류(B-tree, Hash, GIN, GiST)별 특성과
           각 인덱스를 선택해야 하는 상황을 설명하고,
           EXPLAIN ANALYZE 결과를 해석하는 방법을 알려주세요.
domain   : database
goal     : concept
stack    : postgresql
```

---

## 수준 판정 기준

| 수준 | 기준 |
|---|---|
| beginner | 개념 정의 + 단순 사용법 질문 |
| intermediate | 두 개념 비교 + 실전 사용 패턴 질문 |
| advanced | 내부 동작 원리 + 성능/트레이드오프 분석 질문 |

---

## 실험 프로토콜

1. 참가자 1인당 통제 질문 5문항 + 자유 질문 5문항 (총 10문항)
2. 질문 순서 랜덤화
3. 각 질문마다 `/ask` → `/feedback` 순서로 진행
4. `user_choice` + `reason_tags` 필수 입력, `note` 선택 입력
5. 세션 종료 후 `v_pairwise_train` 뷰에서 학습 데이터 추출

---

## API 호출 예시

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "user": { "role": "dev", "level": "beginner" },
    "context": {
      "goal": "concept",
      "stack": "python",
      "constraints": null
    },
    "question": "Python에서 리스트와 딕셔너리의 차이점은 무엇인가요?",
    "domain": "python_basic"
  }'
```

> 통제 질문 사용 시 `question_type` 값은 현재 코드에서 `"free"`로 고정되어 있음.
> 향후 `question_type = "controlled"` 를 명시적으로 전달하려면 API 스키마 확장 필요.
