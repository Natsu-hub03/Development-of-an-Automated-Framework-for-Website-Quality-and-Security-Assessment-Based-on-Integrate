import json
import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, AnyHttpUrl
from sqlalchemy.orm import Session

from database import init_db, wait_for_db, get_db, engine
from models import Scan, ScanResult


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