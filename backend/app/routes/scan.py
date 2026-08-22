"""
Individual scanner endpoints: /scan/wappalyzer, /scan/axe, /scan/lighthouse,
/scan/headers, /scan/zap.

These are tool-level endpoints for testing individual scanners.
DB writes are intentionally omitted — use /scan/standards for persisted results.
"""
import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, AnyHttpUrl

from app.config import ZAP_BASE_URL, ZAP_API_KEY
from services.scanner import run_single_scanner

logger = logging.getLogger("webscan.routes.scan")
router = APIRouter(prefix="/scan", tags=["scan"])


class ScanRequest(BaseModel):
    url: AnyHttpUrl


# ── Wappalyzer ────────────────────────────────────────────────────────────────
@router.post("/wappalyzer")
def scan_wappalyzer(request: ScanRequest):
    url_str = str(request.url)
    try:
        data = run_single_scanner("wappalyzer_scan.js", url_str, timeout=120)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Wappalyzer scan timed out (>120s).")
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute scanner: {e}")

    return {"success": True, "data": data}


# ── Axe-core ──────────────────────────────────────────────────────────────────
@router.post("/axe")
def scan_axe(request: ScanRequest):
    """Run axe-core accessibility scan via Puppeteer."""
    url_str = str(request.url)
    try:
        data = run_single_scanner("axe_scan.js", url_str, timeout=60)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="axe-core scan timed out (>60s).")
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute axe scanner: {e}")

    return {"success": True, "data": data}


# ── Lighthouse ────────────────────────────────────────────────────────────────
@router.post("/lighthouse")
def scan_lighthouse(request: ScanRequest):
    """Run Lighthouse performance/a11y/SEO/best-practices audit."""
    url_str = str(request.url)
    try:
        data = run_single_scanner("lighthouse_scan.js", url_str, timeout=90)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Lighthouse scan timed out (>90s).")
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute Lighthouse: {e}")

    return {"success": True, "data": data}


# ── Headers ───────────────────────────────────────────────────────────────────
@router.post("/headers")
def scan_headers(request: ScanRequest):
    """Run headers/TLS/cookie security scan."""
    url_str = str(request.url)
    try:
        data = run_single_scanner("headers_scan.js", url_str, timeout=60)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Headers scan timed out (>60s).")
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute headers scanner: {e}")

    return {"success": True, "data": data}


# ── ZAP ───────────────────────────────────────────────────────────────────────
@router.post("/zap")
async def scan_zap(request: ScanRequest):
    """Run ZAP spider + active scan. Returns friendly error if ZAP is unavailable."""
    url_str = str(request.url)
    params = {"apikey": ZAP_API_KEY}

    async with httpx.AsyncClient(base_url=ZAP_BASE_URL, timeout=30.0) as client:
        # 0. Check ZAP is reachable
        try:
            await client.get(
                "/JSON/core/action/accessUrl/",
                params={**params, "url": url_str, "followRedirects": "true"},
            )
        except httpx.RequestError:
            return {
                "success": False,
                "error": "ZAP service is not reachable. Make sure Docker is running with `docker-compose up`.",
                "data": None,
            }

        # 1. Start spider
        try:
            resp = await client.get(
                "/JSON/spider/action/scan/", params={**params, "url": url_str}
            )
            spider_data = resp.json()
            scan_id_spider = spider_data.get("scan")
            if scan_id_spider is None:
                raise HTTPException(
                    status_code=502,
                    detail=f"ZAP spider failed to start: {spider_data}",
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, detail=f"ZAP connection lost during spider: {e}"
            )

        # 2. Wait for spider (poll every 2s, max 120s)
        for _ in range(60):
            resp = await client.get(
                "/JSON/spider/view/status/",
                params={**params, "scanId": scan_id_spider},
            )
            status = resp.json().get("status", "0")
            if int(status) >= 100:
                break
            await asyncio.sleep(2)

        # 3. Start active scan
        try:
            resp = await client.get(
                "/JSON/ascan/action/scan/", params={**params, "url": url_str}
            )
            ascan_data = resp.json()
            scan_id_ascan = ascan_data.get("scan")
            if scan_id_ascan is None:
                raise HTTPException(
                    status_code=502,
                    detail=f"ZAP active scan failed to start: {ascan_data}",
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"ZAP connection lost during active scan: {e}",
            )

        # 4. Wait for active scan (poll every 3s, max 300s)
        for _ in range(100):
            resp = await client.get(
                "/JSON/ascan/view/status/",
                params={**params, "scanId": scan_id_ascan},
            )
            status = resp.json().get("status", "0")
            if int(status) >= 100:
                break
            await asyncio.sleep(3)

        # 5. Get alerts
        resp = await client.get(
            "/JSON/alert/view/alerts/", params={**params, "baseurl": url_str}
        )
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

    return {"success": True, "data": result_data}
