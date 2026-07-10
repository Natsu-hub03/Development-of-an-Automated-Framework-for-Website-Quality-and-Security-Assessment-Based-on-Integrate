from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json
from database import SessionLocal
from models import Scan, ScanResult

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    url: str

@app.post("/scan/wappalyzer")
def scan_wappalyzer(request: ScanRequest):
    result = subprocess.run(
        ["node", "../scanner/wappalyzer_scan.js", request.url],
        capture_output=True,
        text=True,
        timeout=120
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