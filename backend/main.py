import json
import os
import subprocess
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyHttpUrl
from sqlalchemy.orm import Session

from database import init_db, wait_for_db, get_db, engine
from models import Scan, ScanResult

# ZAP config — uses Docker service name for internal network
ZAP_BASE_URL = os.getenv("ZAP_BASE_URL", "http://zap:8080")
ZAP_API_KEY = os.getenv("ZAP_API_KEY", "ZapK3yPr0ject2026Sec")


@asynccontextmanager
async def lifespan(app: FastAPI):
    wait_for_db()
    init_db()
    yield
    engine.dispose()


app = FastAPI(lifespan=lifespan)

# Load allowed origins from environment variable, falling back to defaults if not set
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
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

class ScanRequest(BaseModel):
    url: AnyHttpUrl

@app.post("/scan/wappalyzer")
def scan_wappalyzer(request: ScanRequest, db: Session = Depends(get_db)):
    url_str = str(request.url)
    # Look for scanner in backend/scanner (Docker structure) or ../scanner (local structure)
    parent_dir = Path(__file__).resolve().parent
    script_path = parent_dir / "scanner" / "wappalyzer_scan.js"
    if not script_path.exists():
        script_path = parent_dir.parent / "scanner" / "wappalyzer_scan.js"
    
    cwd_path = script_path.parent

    
    try:
        result = subprocess.run(
            ["node", str(script_path), url_str],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(cwd_path),
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scanner command execution timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute scanner: {str(e)}")

    if result.returncode != 0:
        raise HTTPException(status_code=502, detail=f"Scanner execution failed: {result.stderr or result.stdout}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse scanner output. Raw output: {result.stdout}"
        )

    try:
        scan = Scan(url=url_str, status="completed")
        db.add(scan)
        db.commit()
        db.refresh(scan)

        scan_result = ScanResult(
            scan_id=scan.id,
            tool_name="wappalyzer",
            raw_data=data
        )
        db.add(scan_result)
        db.commit()

        return {"success": True, "scan_id": scan.id, "data": data}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database write failed: {str(e)}")


@app.post("/scan/zap")
async def scan_zap(request: ScanRequest, db: Session = Depends(get_db)):
    """Run ZAP spider + active scan on target URL, return vulnerability alerts."""
    url_str = str(request.url)
    params = {"apikey": ZAP_API_KEY}

    async with httpx.AsyncClient(base_url=ZAP_BASE_URL, timeout=30.0) as client:
        # 1. Start spider
        try:
            resp = await client.get("/JSON/spider/action/scan/", params={**params, "url": url_str})
            spider_data = resp.json()
            scan_id_spider = spider_data.get("scan")
            if scan_id_spider is None:
                raise HTTPException(status_code=502, detail=f"ZAP spider failed to start: {spider_data}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Cannot connect to ZAP: {str(e)}")

        # 2. Wait for spider to complete (poll every 2s, max 120s)
        for _ in range(60):
            resp = await client.get("/JSON/spider/view/status/", params={**params, "scanId": scan_id_spider})
            status = resp.json().get("status", "0")
            if int(status) >= 100:
                break
            await asyncio.sleep(2)

        # 3. Start active scan
        try:
            resp = await client.get("/JSON/ascan/action/scan/", params={**params, "url": url_str})
            ascan_data = resp.json()
            scan_id_ascan = ascan_data.get("scan")
            if scan_id_ascan is None:
                raise HTTPException(status_code=502, detail=f"ZAP active scan failed to start: {ascan_data}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Cannot connect to ZAP: {str(e)}")

        # 4. Wait for active scan to complete (poll every 3s, max 300s)
        for _ in range(100):
            resp = await client.get("/JSON/ascan/view/status/", params={**params, "scanId": scan_id_ascan})
            status = resp.json().get("status", "0")
            if int(status) >= 100:
                break
            await asyncio.sleep(3)

        # 5. Get alerts
        resp = await client.get("/JSON/alert/view/alerts/", params={**params, "baseurl": url_str})
        alerts = resp.json().get("alerts", [])

    # Summarize by risk
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

    # Save to DB
    try:
        scan = Scan(url=url_str, status="completed")
        db.add(scan)
        db.commit()
        db.refresh(scan)

        scan_result = ScanResult(
            scan_id=scan.id,
            tool_name="zap",
            raw_data=result_data
        )
        db.add(scan_result)
        db.commit()

        return {"success": True, "scan_id": scan.id, "data": result_data}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database write failed: {str(e)}")