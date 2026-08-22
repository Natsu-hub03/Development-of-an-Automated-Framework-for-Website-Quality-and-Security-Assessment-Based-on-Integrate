"""
WebScan API — FastAPI application entry point.

This file handles only:
  - App creation and lifespan
  - CORS middleware
  - Router registration

All route logic lives in app.routes.*
All config lives in app.config
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from db.database import init_db, wait_for_db, engine
from services.scanner import scanner_executor

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("webscan")


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    init_db()
    logger.info("WebScan API started")
    yield
    scanner_executor.shutdown(wait=False)
    engine.dispose()
    logger.info("WebScan API shut down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="WebScan API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routes.scan import router as scan_router
from app.routes.standards import router as standards_router
from app.routes.ai import router as ai_router
from app.routes.health import router as health_router

app.include_router(scan_router)
app.include_router(standards_router)
app.include_router(ai_router)
app.include_router(health_router)
