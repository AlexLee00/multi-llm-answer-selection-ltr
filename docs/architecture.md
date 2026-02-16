# Architecture (Prototype)

## 1. 전체 흐름

User → /ask →
  - UserAnon 저장
  - Context 저장
  - Question 저장
  - Candidates 생성
  - Rule 선택
  - LTR 선택
  - Selection 저장
  - 응답 반환

→ /feedback →
  - feedback_pairwise 저장

→ ML Pipeline →
  - snapshot 생성
  - export trainset
  - train model
  - register model
  - LTR 서빙

---

## 2. 주요 테이블

users_anon
contexts
questions
candidates
selections
feedback_pairwise
snapshots
models

---

## 3. Rule vs LTR

Rule:
- feature 기반 단순 휴리스틱 선택

LTR:
- pairwise diff feature 입력
- logistic regression 모델 사용
- tournament 방식 평균 확률 계산

---

## 4. Feature v1

- len_words
- has_code
- step_score
- has_bullets
- has_warning

학습 시:
diff = A - B
