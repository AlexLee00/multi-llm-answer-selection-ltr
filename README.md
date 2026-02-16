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

1. Generate candidate answers from multiple LLM providers
2. Extract lightweight features (v1 → v2 expansion)
3. Select best answer via:

   * Rule baseline
   * LTR model
4. Collect structured pairwise feedback
5. Train batch ranking pipeline
6. Deploy latest model automatically for serving

---

# 🏗 Architecture (High-Level)

Client
→ API `/ask`
→ Candidate Generation (N providers)
→ Feature Extraction
→ Selector Layer (Rule / LTR)
→ Selection 저장

Client
→ API `/feedback`
→ Pairwise label 저장

Batch Training Pipeline
→ Snapshot
→ Trainset Export
→ Model Train
→ Model Register
→ LTR Serving

---

# 📂 Repository Structure

```
docs/design/        # SE design artifacts
infra/              # Docker Compose (Postgres)
apps/api/           # FastAPI service + Alembic + src
artifacts/          # trainsets + trained models
```

---

# 🚀 Quick Start (Local)

## 1️⃣ Start Postgres

```bash
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps
```

---

## 2️⃣ DB Migration

```bash
alembic upgrade head
```

Verify tables:

```bash
docker exec -it mlas_postgres psql -U mlas -d mlas -c "\dt"
```

Expected:

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

## 3️⃣ Run API

```bash
uvicorn src.app.main:app --reload
```

Swagger:

```
http://localhost:8000/docs
```

---

# 🔁 End-to-End Flow

## Step 1 — Ask

Set environment:

```
SERVED_POLICY=rule
# or
SERVED_POLICY=ltr
```

Call `/ask`

Response includes:

* question_id
* candidate_a_id
* candidate_b_id
* served_choice_candidate_id

---

## Step 2 — Feedback

Call `/feedback`:

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

Stored in:

* feedback_pairwise
* v_pairwise_train (view)

---

# 🧠 ML Pipeline

## 1️⃣ Snapshot

```bash
python scripts/make_snapshot.py
```

Stores:

* snapshot_id
* row_count
* data_range_json

---

## 2️⃣ Export Trainset

```bash
python scripts/export_trainset.py
```

Outputs:

```
artifacts/trainsets/<snapshot_id>.csv
artifacts/trainsets/<snapshot_id>.jsonl
```

---

## 3️⃣ Train Model

```bash
python scripts/train_baseline.py
```

* Logistic Regression
* Dummy fallback if single class
* Stores:

  * .pkl
  * metadata .json

---

## 4️⃣ Register Model

```bash
python scripts/register_model.py
```

Stored in `models` table:

* model_version
* snapshot_id
* feature_version
* metrics_json
* artifact_path
* trained_at

---

# 🏁 LTR Serving Logic

At runtime:

1. Load ACTIVE_MODEL_VERSION (if set)
2. Otherwise select latest trained model
3. Cache model in memory
4. Perform pairwise tournament scoring
5. Select highest average win probability

Selection row records:

* rule_choice_candidate_id
* ltr_choice_candidate_id
* served_choice_candidate_id
* served_policy
* model_version

---

# 📊 Feature Design

## v1 (Implemented)

* len_words
* has_code
* step_score
* has_bullets
* has_warning

Training input:

```
diff = A_features - B_features
```

---

## v2 (Planned)

* semantic similarity (question ↔ answer)
* embedding cosine distance
* hallucination risk indicators
* structural completeness score

---

# 🧪 Research Setup (Pilot)

Participants: 30
Per participant: ~10 questions

Controlled mix:

* Beginner ×2
* Intermediate ×2
* Advanced ×1
* Free-form questions

---

# 📈 Evaluation Metrics

* Rank Accuracy
* NDCG@1
* Improvement over Rule baseline
* Agreement with human preference

---

# ⚙ Environment Configuration

`.env`

```
DB_URL=postgresql+psycopg2://mlas:mlas_pw@localhost:5432/mlas
SERVED_POLICY=ltr
ACTIVE_MODEL_VERSION=
```

* SERVED_POLICY: rule | ltr
* ACTIVE_MODEL_VERSION: pin specific model (optional)

---

# ✅ Current Prototype Status

✔ DB schema complete
✔ Pairwise feedback pipeline working
✔ Snapshot/export/train/register pipeline working
✔ Model registry functional
✔ LTR serving integrated
✔ Rule vs LTR comparison possible

---

# 🔜 Next Phase

1. Feature v2 expansion
2. Controlled experiment execution
3. Statistical significance testing
4. Incremental retraining strategy
5. Research paper structuring

---

# 📄 Design Documentation

Located in:

```
docs/design/
```

Includes:

* architecture.md
* data-schema.md
* api-contract.md
* pipeline.md
* threat-privacy.md
* controlled-questions.md
* rtm.md

---

# 📜 License

MIT