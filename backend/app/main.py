"""
main.py — FastAPI application entrypoint.

Local dev:   uvicorn app.main:app --reload
Production:  Started by Render via render.yaml startCommand
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth, subjects, papers, analysis, predictions, chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("pdfminer").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Question Paper Analyzer & Predictor",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Reads FRONTEND_URL from environment so we can add the Vercel URL on Render
# without editing code. Falls back to localhost for local dev.
_frontend_url = os.getenv("FRONTEND_URL", "")
_allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if _frontend_url:
    _allowed_origins.append(_frontend_url)
# Also allow all Vercel preview URLs (*.vercel.app)
_allow_origin_regex = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(subjects.router)
app.include_router(papers.router)
app.include_router(analysis.router)
app.include_router(predictions.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "service": "AI Question Paper Analyzer & Predictor",
        "version": "1.0.0",
    }
