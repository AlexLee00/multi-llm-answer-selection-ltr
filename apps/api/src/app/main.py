from fastapi import FastAPI
from src.app.routers.ask import router as ask_router

app = FastAPI(title="Multi-LLM Answer Selection API")

app.include_router(ask_router)

@app.get("/health")
def health():
    return {"status": "ok"}
