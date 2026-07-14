import json
import subprocess
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import SessionLocal, init_db, wait_for_db
from models import Scan, ScanResult

app = FastAPI()


@app.on_event("startup")
def startup_event():
    wait_for_db()
    init_db()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    url: str

@app.post("/scan/wappalyzer")
def scan_wappalyzer(request: ScanRequest):
    script_path = Path(__file__).resolve().parent / "scanner" / "wappalyzer_scan.js"
    result = subprocess.run(
        ["node", str(script_path), request.url],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(Path(__file__).resolve().parent),
    )
    if result.returncode != 0:
        return {"error": result.stderr}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "failed to parse result", "raw": result.stdout}

    db = SessionLocal()
    try:
        scan = Scan(url=request.url, status="completed")
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
    finally:
        db.close()