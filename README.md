# multi-llm-answer-selection-ltr

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-API-green.svg)
![Postgres](https://img.shields.io/badge/PostgreSQL-16-blue)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Research](https://img.shields.io/badge/Research-LTR-orange.svg)


Research platform for **multi-LLM answer selection** using **Learning-to-Rank (LTR)**.

The system generates candidate answers from multiple LLM providers (initially: ChatGPT API + Gemini API),  
collects **pairwise human feedback**, and trains a **ranker** to recommend the best response for IT learners.

> **Target users:** University students across roles (planner / designer / developer / tester), not necessarily developers.  
> **Goal:** Performance-driven selection quality improvement for KCI-level evaluation.

---

## Key Idea

1. **Generate** candidate answers from N LLM providers  
2. **Extract** lightweight features  
   - v1: structural / format features  
   - v2: semantic matching features  
3. **Select** best answer using rule baseline → LTR model  
4. **Collect** pairwise feedback (A/B/tie/bad + reason tags)  
5. **Train** batch pipeline (later: incremental updates)

---

## Project Status

- [x] Requirements / Concept lock (analysis completed)
- [x] DB schema + Alembic migrations (Postgres)
- [x] Docker Postgres (local)
- [ ] API service (FastAPI) `/ask` + `/feedback`
- [ ] Candidate generation adapters (OpenAI, Gemini)
- [ ] Feature extraction v1
- [ ] Rule baseline selector
- [ ] Ranker training (batch) + model registry
- [ ] Reports (rank accuracy, NDCG@1, improvements)

---

## Architecture (High-Level)

```

Client
→ API (/ask)
→ Generator Layer (N providers)
→ Selector Layer (Rule / LTR)
→ Storage (Postgres + JSONL archive)

→ API (/feedback)
→ Pairwise labels stored

Training Pipeline (batch)
→ snapshot
→ feature build
→ train
→ evaluate
→ release

```

---

## Repo Structure

```

docs/design/        # SE design artifacts (analysis/design phase)
infra/              # Local infrastructure (Docker Compose)
apps/api/           # FastAPI service + Alembic + src

````

---

## Quick Start (Local)

### 1) Start Postgres

```bash
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps
````

### 2) Verify DB Tables

```bash
docker exec -it mlas_postgres psql -U mlas -d mlas -c "\dt"
```

Expected tables:

* users_anon
* questions
* contexts
* candidates
* selections
* feedback_pairwise
* snapshots
* models
* alembic_version

---

## Design Docs

* `docs/design/architecture.md`
* `docs/design/data-schema.md`
* `docs/design/api-contract.md`
* `docs/design/pipeline.md`
* `docs/design/threat-privacy.md`
* `docs/design/controlled-questions.md`
* `docs/design/rtm.md`

---

## Research Setup (Pilot)

* Participants: 30
* Per participant: ~10 questions
* Question mix: controlled + free
* Controlled difficulty mix:

  * Beginner: 2
  * Intermediate: 2
  * Advanced: 1

**Evaluation Metrics**

* Rank Accuracy
* NDCG@1
* Improvement over baselines

---

## License

MIT

```

---

## 🔥 수정 포인트 요약

✔ 코드블록 닫힘 오류 수정  
✔ Architecture 구조를 트리 형식으로 가독성 향상  
✔ Repo Structure 코드블록 처리  
✔ Research Setup 계층화  
✔ Evaluation Metrics 강조  
✔ GitHub에서 예쁘게 보이도록 간격 조정  

---

이제 이 상태로 커밋하면 문서 완성도 상당히 높다.

---

**Q1**

README에 “실험 프로토콜 상세(통제 질문 예시)”를 바로 넣을까, 아니면 design 폴더로 분리할까?  

  
**Q2**

Architecture 다이어그램을 ASCII 대신 이미지로 넣을까?  

  
**Q3**

GitHub 상단에 배지(Badge: Python, FastAPI, Postgres, MIT)도 추가할까?
```
