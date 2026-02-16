# Changelog (Prototype)

## Added
- /ask response includes pairwise ids for quick /feedback testing:
  - question_id, candidate_a_id, candidate_b_id, served_choice_candidate_id
- v_pairwise_train view for training data extraction
- ML pipeline scripts:
  - scripts/make_snapshot.py
  - scripts/export_trainset.py
  - scripts/train_baseline.py
  - scripts/register_model.py
- LTR ranker service with model cache and newest-model selection

## Changed
- schemas.py migrated to Enum-based validation (Swagger dropdown)
- /feedback request fields aligned to DB columns:
  - candidate_a_id, candidate_b_id, user_choice, reason_tags, note
- /ask transaction optimized to flush() and single commit()
- selections table now stores:
  - rule_choice_candidate_id, ltr_choice_candidate_id, served_choice_candidate_id, served_policy
  - model_version (when LTR served)

## Environment
- SERVED_POLICY=rule|ltr
- ACTIVE_MODEL_VERSION=<optional>
- DB_URL required by scripts

## Known Issues / Notes
- Training requires at least 2 classes; fallback to DummyClassifier when only one class
- Small dataset yields unstable accuracy; collect more pairwise feedback for meaningful metrics
