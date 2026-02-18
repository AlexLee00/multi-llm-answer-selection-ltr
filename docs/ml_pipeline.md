# ML Pipeline

## 개요

```
feedback_pairwise 수집
  → make_snapshot   : 데이터 범위 스냅샷
  → export_trainset : CSV / JSONL 추출
  → train_baseline  : 모델 학습
  → register_model  : DB 등록
  → LTR Serving     : ranker.py 자동 로드
```

---

## 1. Data Source

**뷰**: `v_pairwise_train`

- `feedback_pairwise` JOIN `candidates` (A, B)
- 조건: `user_choice IN ('a', 'b')` (tie/bad 제외)
- feature_version = "fv1"

**fv1 특징 컬럼**:

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `len_words` | int | 단어 수 |
| `has_code` | bool | 코드블록 포함 여부 |
| `step_score` | int | 단계형 설명 포함 여부 |
| `has_bullets` | bool | 불릿 포함 여부 |
| `has_warning` | bool | 경고 문구 포함 여부 |

학습 입력: `X = A_features - B_features` (pairwise diff, 5차원)
레이블: `y = 1` (A 선호) / `y = 0` (B 선호)

---

## 2. Snapshot (`make_snapshot.py`)

`snapshots` 테이블에 저장:

```
snapshot_id   : UUID (자동 생성)
data_range_json : {"min_date": ..., "max_date": ..., "n_rows": ...}
row_count     : 집계된 학습 행 수
created_at    : 스냅샷 생성 시각
```

실행:
```bash
cd apps/api
python scripts/make_snapshot.py
```

---

## 3. Export Trainset (`export_trainset.py`)

스냅샷 ID를 기반으로 학습 데이터 추출:

출력 경로:
```
artifacts/trainsets/<snapshot_id>.csv
artifacts/trainsets/<snapshot_id>.jsonl
```

CSV 컬럼 예시:
```
snapshot_id, candidate_a_id, candidate_b_id,
len_words_diff, has_code_diff, step_score_diff, has_bullets_diff, has_warning_diff,
label
```

실행:
```bash
python scripts/export_trainset.py --snapshot-id <snapshot_id>
```

---

## 4. Train Baseline (`train_baseline.py`)

**모델**: `LogisticRegression` (sklearn)
- 입력: pairwise diff 5차원 feature
- 단일 클래스 데이터 → `DummyClassifier` fallback

**저장 경로**:
```
artifacts/models/<model_version>.pkl   # 학습된 모델
artifacts/models/<model_version>.json  # 메타데이터 (metrics 포함)
```

**metrics_json 예시**:
```json
{
  "accuracy": 0.75,
  "n_train": 80,
  "n_test": 20,
  "feature_version": "fv1"
}
```

실행:
```bash
python scripts/train_baseline.py --snapshot-id <snapshot_id>
```

---

## 5. Register Model (`register_model.py`)

`models` 테이블에 등록:

| 컬럼 | 설명 |
|---|---|
| `model_version` | 버전 식별자 (예: `v1-20240201`) |
| `snapshot_id` | 학습에 사용된 스냅샷 |
| `feature_version` | `fv1` |
| `metrics_json` | accuracy 등 성능 지표 |
| `artifact_path` | `.pkl` 파일 경로 |
| `trained_at` | 등록 시각 |

실행:
```bash
python scripts/register_model.py \
  --model-version <version> \
  --snapshot-id <snapshot_id> \
  --artifact-path artifacts/models/<version>.pkl \
  --metrics-json artifacts/models/<version>.json
```

---

## 6. LTR Serving (`ranker.py`)

### 모델 로드 순서

```
1. ACTIVE_MODEL_VERSION 환경변수 확인
   → 설정된 경우 해당 버전 로드

2. 미설정인 경우 → models 테이블에서 trained_at DESC limit 1 조회

3. 프로세스 메모리 캐시 (_MODEL_CACHE)
   → 버전 변경 시 자동 갱신
```

### 선택 알고리즘 (tournament)

```python
for i, a in enumerate(candidates):
    for j, b in enumerate(candidates):
        if i == j: continue
        x = features(a) - features(b)   # pairwise diff
        p = predict_proba(x)[0, 1]       # P(A wins)
        p_list.append(p)
    probs[i] = mean(p_list)              # 평균 win probability

best = candidates[argmax(probs)]
```

### 반환값

```python
(best_candidate, model_version, error_message)

# 모델 없음  → (None, None, "no_model")
# 후보 없음  → (None, mv,   "no_candidates")
# 후보 1개   → (candidates[0], mv, None)  # trivially best
# 실패       → (None, mv,   "error: ...")
```

### 환경변수

| 변수 | 설명 |
|---|---|
| `ACTIVE_MODEL_VERSION` | 특정 버전 고정 (미설정 시 최신 자동) |
| `SERVED_POLICY` | `ltr` 로 설정해야 LTR 서빙 활성화 |
