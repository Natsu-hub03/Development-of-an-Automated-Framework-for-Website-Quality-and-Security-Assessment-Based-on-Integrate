"""
Centralized configuration — all environment variables and constants.
"""
import os

# ── Service URLs ──────────────────────────────────────────────────────────────
ZAP_BASE_URL    = os.getenv("ZAP_BASE_URL",    "http://localhost:8080")
ZAP_API_KEY     = os.getenv("ZAP_API_KEY",      "change-me-in-env-file")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL",  "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",     "qwen2.5:3b")

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    ALLOWED_ORIGINS = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

# ── AI Prompt ─────────────────────────────────────────────────────────────────
MAX_JSON_CHARS = 3000
