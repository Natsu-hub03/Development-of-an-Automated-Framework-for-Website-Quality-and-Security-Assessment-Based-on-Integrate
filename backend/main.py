import json
import os
import subprocess
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

# pyrefly: ignore [missing-import]
import httpx
import ollama
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyHttpUrl
from sqlalchemy.orm import Session

from database import init_db, wait_for_db, get_db, engine
from models import Scan, ScanResult

# ── Config ────────────────────────────────────────────────────────────────────
ZAP_BASE_URL   = os.getenv("ZAP_BASE_URL",   "http://zap:8080")
ZAP_API_KEY    = os.getenv("ZAP_API_KEY",    "ZapK3yPr0ject2026Sec")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3.2:3b")

# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    init_db()
    yield
    engine.dispose()


app = FastAPI(title="WebScan API", version="1.0.0", lifespan=lifespan)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ──────────────────────────────────────────────────
class ScanRequest(BaseModel):
    url: AnyHttpUrl


class AIAnalyzeRequest(BaseModel):
    url: str
    scan_data: Any          # raw scan result (wappalyzer, zap, or combined)
    scan_type: str = "both" # "wappalyzer" | "zap" | "both"


# ── Helper: resolve scanner path ───────────────────────────────────────────────
def _get_scanner_path() -> Path:
    parent = Path(__file__).resolve().parent
    candidate = parent / "scanner" / "wappalyzer_scan.js"
    if candidate.exists():
        return candidate
    fallback = parent.parent / "scanner" / "wappalyzer_scan.js"
    if fallback.exists():
        return fallback
    raise FileNotFoundError("wappalyzer_scan.js not found")


# ── Wappalyzer scan ────────────────────────────────────────────────────────────
@app.post("/scan/wappalyzer")
def scan_wappalyzer(request: ScanRequest, db: Session = Depends(get_db)):
    url_str = str(request.url)

    try:
        script_path = _get_scanner_path()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        proc = subprocess.run(
            ["node", str(script_path), url_str],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(script_path.parent),
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Wappalyzer scan timed out (>120s).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute scanner: {e}")

    # Parse stdout — always JSON now (both success & error cases)
    raw_output = proc.stdout.strip()
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        detail = f"Unexpected scanner output: {raw_output[:300]}"
        if proc.stderr:
            detail += f" | stderr: {proc.stderr[:200]}"
        raise HTTPException(status_code=500, detail=detail)

    # If the scanner itself reported an error (exitCode=1 + {error:...})
    if proc.returncode != 0:
        raise HTTPException(
            status_code=502,
            detail=data.get("error", f"Scanner failed: {raw_output[:300]}")
        )

    # Persist to DB
    try:
        scan = Scan(url=url_str, status="completed")
        db.add(scan)
        db.commit()
        db.refresh(scan)

        scan_result = ScanResult(scan_id=scan.id, tool_name="wappalyzer", raw_data=data)
        db.add(scan_result)
        db.commit()

        return {"success": True, "scan_id": scan.id, "data": data}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database write failed: {e}")


# ── ZAP scan ───────────────────────────────────────────────────────────────────
@app.post("/scan/zap")
async def scan_zap(request: ScanRequest, db: Session = Depends(get_db)):
    """Run ZAP spider + active scan. Returns friendly error if ZAP is unavailable."""
    url_str = str(request.url)
    params  = {"apikey": ZAP_API_KEY}

    async with httpx.AsyncClient(base_url=ZAP_BASE_URL, timeout=30.0) as client:
        # 0. Check ZAP is reachable
        try:
            await client.get(
                "/JSON/core/action/accessUrl/",
                params={**params, "url": url_str, "followRedirects": "true"},
            )
        except httpx.RequestError:
            # ZAP not running — return a user-friendly error payload instead of 503
            return {
                "success": False,
                "error": "ZAP service is not reachable. Make sure Docker is running with `docker-compose up`.",
                "data": None,
            }

        # 1. Start spider
        try:
            resp = await client.get("/JSON/spider/action/scan/", params={**params, "url": url_str})
            spider_data   = resp.json()
            scan_id_spider = spider_data.get("scan")
            if scan_id_spider is None:
                raise HTTPException(status_code=502, detail=f"ZAP spider failed to start: {spider_data}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"ZAP connection lost during spider: {e}")

        # 2. Wait for spider (poll every 2s, max 120s)
        for _ in range(60):
            resp   = await client.get("/JSON/spider/view/status/", params={**params, "scanId": scan_id_spider})
            status = resp.json().get("status", "0")
            if int(status) >= 100:
                break
            await asyncio.sleep(2)

        # 3. Start active scan
        try:
            resp = await client.get("/JSON/ascan/action/scan/", params={**params, "url": url_str})
            ascan_data    = resp.json()
            scan_id_ascan = ascan_data.get("scan")
            if scan_id_ascan is None:
                raise HTTPException(status_code=502, detail=f"ZAP active scan failed to start: {ascan_data}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"ZAP connection lost during active scan: {e}")

        # 4. Wait for active scan (poll every 3s, max 300s)
        for _ in range(100):
            resp   = await client.get("/JSON/ascan/view/status/", params={**params, "scanId": scan_id_ascan})
            status = resp.json().get("status", "0")
            if int(status) >= 100:
                break
            await asyncio.sleep(3)

        # 5. Get alerts
        resp   = await client.get("/JSON/alert/view/alerts/", params={**params, "baseurl": url_str})
        alerts = resp.json().get("alerts", [])

    risk_summary = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    for alert in alerts:
        risk = alert.get("risk", "Informational")
        risk_summary[risk] = risk_summary.get(risk, 0) + 1

    result_data = {
        "url": url_str,
        "total_alerts": len(alerts),
        "risk_summary": risk_summary,
        "alerts": alerts,
    }

    try:
        scan = Scan(url=url_str, status="completed")
        db.add(scan)
        db.commit()
        db.refresh(scan)

        scan_result = ScanResult(scan_id=scan.id, tool_name="zap", raw_data=result_data)
        db.add(scan_result)
        db.commit()

        return {"success": True, "scan_id": scan.id, "data": result_data}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database write failed: {e}")


# ── AI Analysis ────────────────────────────────────────────────────────────────
@app.post("/analyze/ai")
async def analyze_with_ai(request: AIAnalyzeRequest):
    """
    Send scan results to Ollama (local LLM) for security analysis.
    Returns a structured markdown report.
    """
    # Build prompt — truncate scan data to avoid context overflow on small models
    MAX_JSON_CHARS = 3000
    scan_json = json.dumps(request.scan_data, ensure_ascii=False, indent=2)
    if len(scan_json) > MAX_JSON_CHARS:
        scan_json = scan_json[:MAX_JSON_CHARS] + "\n... (truncated)"

    prompt = f"""You are an expert web application security analyst.

Analyze the following scan results for the website: {request.url}
Scan type: {request.scan_type}

Scan data:
{scan_json}

Provide a security analysis report in markdown with these sections:
1. Executive Summary (2-3 sentences)
2. Detected Technologies and security implications
3. Vulnerabilities and Risks (Risk Level, Issue, Impact, Recommendation)
4. Top 5 Security Recommendations
5. Overall Risk Score 1-10 with justification

Use Thai for descriptions, keep technical terms in English.
"""

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_ctx": 4096,
                "num_predict": 1024,
                "temperature": 0.7,
            },
        )
        analysis_text = response.response
    except ollama.ResponseError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama model error: {e.error}. Make sure model '{OLLAMA_MODEL}' is pulled: `ollama pull {OLLAMA_MODEL}`"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not reachable at {OLLAMA_BASE_URL}. Install from https://ollama.com and run: ollama pull {OLLAMA_MODEL}"
        )

    return {
        "success": True,
        "url": request.url,
        "model": OLLAMA_MODEL,
        "analysis": analysis_text,
    }


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}