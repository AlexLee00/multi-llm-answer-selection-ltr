# ML Pipeline

## 1. Data Source

View:
v_pairwise_train

조건:
user_choice in ('a','b')

---

## 2. Snapshot

snapshots 테이블에:
- snapshot_id
- data_range_json
- row_count 저장

---

## 3. Export

artifacts/trainsets/<snapshot_id>.csv
artifacts/trainsets/<snapshot_id>.jsonl

---

## 4. Train

- baseline: LogisticRegression
- 1 class only → DummyClassifier fallback

저장:
artifacts/models/<model_version>.pkl
artifacts/models/<model_version>.json

---

## 5. Register

models 테이블에:

- model_version
- snapshot_id
- feature_version
- metrics_json (jsonb)
- artifact_path

---

## 6. LTR Serving

ranker.py:

- 최신 model_version 자동 조회
- 모델 캐시
- 후보간 pairwise diff 계산
- 평균 win prob 기반 선택
