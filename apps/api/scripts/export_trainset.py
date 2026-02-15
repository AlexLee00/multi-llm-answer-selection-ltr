from __future__ import annotations

import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = os.getenv("DB_URL", "")
if not DB_URL:
    raise RuntimeError("DB_URL is empty. Set it in apps/api/.env")


def main() -> None:
    engine = create_engine(DB_URL, future=True)

    # 최신 snapshot_id 1개 가져오기
    with engine.begin() as conn:
        snapshot_id = conn.execute(
            text("""
                select snapshot_id
                from snapshots
                order by created_at desc
                limit 1;
            """)
        ).scalar_one()

    # ✅ 이미 v_pairwise_train에 학습용 컬럼이 다 있으니 join 없이 그대로 export
    # - a_* / b_* feature
    # - user_choice / served_policy
    # - winner/loser candidate_id
    df = pd.read_sql(
        text("""
            select
                feedback_id,
                feedback_at,
                question_id,
                candidate_a_id,
                candidate_b_id,

                a_provider, a_model, a_len_words, a_has_code, a_step_score, a_has_bullets, a_has_warning,
                b_provider, b_model, b_len_words, b_has_code, b_step_score, b_has_bullets, b_has_warning,

                user_choice,
                served_policy,
                served_choice_candidate_id,
                winner_candidate_id,
                loser_candidate_id
            from v_pairwise_train
            where user_choice in ('a','b')
            order by feedback_at desc;
        """),
        engine,
    )

    out_dir = Path("artifacts/trainsets")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir / f"{snapshot_id}.csv"
    out_jsonl = out_dir / f"{snapshot_id}.jsonl"

    df.to_csv(out_csv, index=False, encoding="utf-8")

    with out_jsonl.open("w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            f.write(json.dumps(row.to_dict(), ensure_ascii=False, default=str) + "\n")

    print("✅ Trainset exported")
    print(f"- snapshot_id: {snapshot_id}")
    print(f"- rows      : {len(df)}")
    print(f"- csv       : {out_csv}")
    print(f"- jsonl     : {out_jsonl}")


if __name__ == "__main__":
    main()
