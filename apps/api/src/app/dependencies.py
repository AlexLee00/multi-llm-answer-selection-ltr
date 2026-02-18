from __future__ import annotations

import os
from pathlib import Path
 
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# .env는 이 파일(src/app/dependencies.py) 기준으로 두 단계 위인 apps/api에 위치
# parents[0] = src/app/, parents[1] = src/, parents[2] = apps/api/
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=_ENV_FILE)  # 파일 기준 절대경로로 항상 정확히 로드

DATABASE_URL = os.getenv("DB_URL")
# DB_URL 누락 시 명확한 RuntimeError (어디서 찾았는지 경로 포함)
if not DATABASE_URL:
    raise RuntimeError(
        f"DB_URL is not set. Checked .env at: {_ENV_FILE}\n"
        "Set DB_URL in .env or as an environment variable."
    )
    
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
