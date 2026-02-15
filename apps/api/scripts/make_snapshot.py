from __future__ import annotations

import os
import json
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = os.getenv("DB_URL", "")
if not DB_URL:
    raise RuntimeError("DB_URL is empty. Set it in apps/api/.env")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    engine = create_engine(DB_URL, future=True)

    count_sql = text("""
        select count(*) as n
        from v_pairwise_train
        where user_choice in ('a','b');
    """)

    insert_sql = text("""
        insert into snapshots (snapshot_id, data_range_json, row_count)
        values (:snapshot_id, cast(:data_range_json as jsonb), :row_count);
    """)

    with engine.begin() as conn:
        n = conn.execute(count_sql).scalar_one()

        snapshot_id = uuid.uuid4()
        payload = {
            "snapshot_id": str(snapshot_id),
            "created_at": utc_now_iso(),
            "source_view": "v_pairwise_train",
            "filter": "user_choice in ('a','b')",
            "row_count": int(n),
        }

        conn.execute(
            insert_sql,
            {
                "snapshot_id": str(snapshot_id),
                "data_range_json": json.dumps(payload, ensure_ascii=False),
                "row_count": int(n),
            },
        )

    print("✅ Snapshot created")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
