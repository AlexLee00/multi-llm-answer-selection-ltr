# apps/api/src/app/main.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.routers.ask import router as ask_router
from src.app.routers.feedback import router as feedback_router
from src.app.services.llm.registry import build_default_registry


APP_TITLE = "Multi-LLM Answer Selection API"
APP_VERSION = "0.1.0"
API_PREFIX = "/api/v1"

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
)

# CORS (local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_prefix": API_PREFIX,
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Routers
app.include_router(ask_router, prefix=API_PREFIX, tags=["ask"])
app.include_router(feedback_router, prefix=API_PREFIX, tags=["feedback"])

@app.on_event("startup")
def startup():
    build_default_registry()
    print("[BOOT] LLM registry initialized")

