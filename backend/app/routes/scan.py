"""
Individual scanner endpoints: /scan/wappalyzer, /scan/axe, /scan/lighthouse,
/scan/headers, /scan/zap.

These are tool-level endpoints for testing individual scanners.
DB writes are intentionally omitted — use /scan/standards for persisted results.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, AnyHttpUrl

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
    """Run optimized ZAP spider + targeted active scan.
    Uses the shared optimized scanner with shallow spider + XSS/SQLi focus.
    """
    from services.scanner import run_zap_scan

    url_str = str(request.url)
    result = await run_zap_scan(url_str)

    if result is None:
        return {
            "success": False,
            "error": "ZAP service is not reachable. Make sure Docker is running with `docker-compose up`.",
            "data": None,
        }

    return {"success": True, "data": result}

