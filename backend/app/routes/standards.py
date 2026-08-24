"""
Standards compliance endpoints:
  POST /scan/standards       — all 68 items
  POST /scan/standard/{id}   — single standard (wcag, cwv, ncsa, owasp)
"""
import asyncio
import logging
from functools import partial

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import ScanRequest
from db.database import get_db
from db.models import Scan, ScanResult
from services.scanner import run_node_scanner, run_zap_scan, scanner_executor
from services.standards import (
    build_standards_report,
    build_single_standard_report,
    STANDARD_TOOLS,
    VALID_STANDARD_IDS,
)

logger = logging.getLogger("webscan.routes.standards")
router = APIRouter(prefix="/scan", tags=["standards"])


STANDARD_LABELS = {
    "wcag": "WCAG 2.1",
    "cwv": "Core Web Vitals & SEO",
    "ncsa": "สกมช.",
    "owasp": "OWASP Headers",
}


@router.post("/standards")
async def scan_standards(request: ScanRequest, db: Session = Depends(get_db)):
    """Run all scanners and produce the 68-item standards compliance report."""
    url_str = str(request.url)
    loop = asyncio.get_running_loop()

    # Run Node.js scanners in thread pool + ZAP async concurrently
    axe_future = loop.run_in_executor(
        scanner_executor, partial(run_node_scanner, "axe_scan.js", url_str, 90)
    )
    lh_future = loop.run_in_executor(
        scanner_executor,
        partial(run_node_scanner, "lighthouse_scan.js", url_str, 120),
    )
    hdr_future = loop.run_in_executor(
        scanner_executor, partial(run_node_scanner, "headers_scan.js", url_str, 60)
    )
    wap_future = loop.run_in_executor(
        scanner_executor,
        partial(run_node_scanner, "wappalyzer_scan.js", url_str, 120),
    )
    zap_task = asyncio.create_task(run_zap_scan(url_str))

    # Await all
    axe_data, lh_data, hdr_data, wap_data, zap_data = await asyncio.gather(
        axe_future, lh_future, hdr_future, wap_future, zap_task
    )

    # Build report
    report = build_standards_report(
        url=url_str,
        axe_data=axe_data,
        lighthouse_data=lh_data,
        headers_data=hdr_data,
        wappalyzer_data=wap_data,
        zap_data=zap_data,
    )

    # Include raw wappalyzer data for tech table
    report["wappalyzer_technologies"] = (
        wap_data.get("technologies", []) if isinstance(wap_data, dict) else []
    )

    # Persist — wrap sync DB ops in executor to avoid blocking the event loop
    def _persist_scan():
        try:
            scan = Scan(url=url_str, status="completed")
            db.add(scan)
            db.commit()
            db.refresh(scan)

            scan_result = ScanResult(
                scan_id=scan.id, tool_name="standards", raw_data=report
            )
            db.add(scan_result)
            db.commit()
            return scan.id
        except Exception as e:
            db.rollback()
            raise e

    try:
        scan_id = await loop.run_in_executor(None, _persist_scan)
        return {"success": True, "scan_id": scan_id, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write failed: {e}")


@router.post("/standard/{standard_id}")
async def scan_single_standard(
    standard_id: str,
    request: ScanRequest,
    db: Session = Depends(get_db),
):
    """Run only the tools needed for a specific standard and return its checklist."""
    if standard_id not in VALID_STANDARD_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown standard: {standard_id}. Valid: {', '.join(sorted(VALID_STANDARD_IDS))}",
        )

    url_str = str(request.url)
    tools_needed = STANDARD_TOOLS[standard_id]
    loop = asyncio.get_running_loop()

    # Run only the tools this standard requires
    futures = []
    future_keys = []

    if "axe" in tools_needed:
        futures.append(
            loop.run_in_executor(
                scanner_executor,
                partial(run_node_scanner, "axe_scan.js", url_str, 90),
            )
        )
        future_keys.append("axe")

    if "lighthouse" in tools_needed:
        futures.append(
            loop.run_in_executor(
                scanner_executor,
                partial(run_node_scanner, "lighthouse_scan.js", url_str, 120),
            )
        )
        future_keys.append("lighthouse")

    if "headers" in tools_needed:
        futures.append(
            loop.run_in_executor(
                scanner_executor,
                partial(run_node_scanner, "headers_scan.js", url_str, 60),
            )
        )
        future_keys.append("headers")

    if "wappalyzer" in tools_needed:
        futures.append(
            loop.run_in_executor(
                scanner_executor,
                partial(run_node_scanner, "wappalyzer_scan.js", url_str, 120),
            )
        )
        future_keys.append("wappalyzer")

    if "zap" in tools_needed:
        futures.append(asyncio.create_task(run_zap_scan(url_str)))
        future_keys.append("zap")

    results = await asyncio.gather(*futures)

    # Map results back
    result_map = dict(zip(future_keys, results))
    axe_data = result_map.get("axe")
    lh_data = result_map.get("lighthouse")
    hdr_data = result_map.get("headers")
    wap_data = result_map.get("wappalyzer")
    zap_data = result_map.get("zap")

    # Build single-standard report
    report = build_single_standard_report(
        standard_id=standard_id,
        url=url_str,
        axe_data=axe_data,
        lighthouse_data=lh_data,
        headers_data=hdr_data,
        wappalyzer_data=wap_data,
        zap_data=zap_data,
    )

    # Include raw wappalyzer data for tech table (relevant for ncsa)
    if wap_data and isinstance(wap_data, dict):
        report["wappalyzer_technologies"] = wap_data.get("technologies", [])
    else:
        report["wappalyzer_technologies"] = []

    # Persist — wrap sync DB ops in executor to avoid blocking the event loop
    def _persist_scan():
        try:
            scan = Scan(url=url_str, status="completed")
            db.add(scan)
            db.commit()
            db.refresh(scan)

            scan_result = ScanResult(
                scan_id=scan.id,
                tool_name=f"standard_{standard_id}",
                raw_data=report,
            )
            db.add(scan_result)
            db.commit()
            return scan.id
        except Exception as e:
            db.rollback()
            raise e

    try:
        scan_id = await loop.run_in_executor(None, _persist_scan)
        return {"success": True, "scan_id": scan_id, "data": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database write failed: {e}")
