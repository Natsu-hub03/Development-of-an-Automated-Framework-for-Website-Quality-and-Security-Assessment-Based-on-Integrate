"""
Scanner subprocess management.

Runs Node.js scanner scripts as child processes and manages the shared
thread pool executor for concurrent scanning.
"""
import json
import asyncio
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import httpx

from app.config import ZAP_BASE_URL, ZAP_API_KEY

logger = logging.getLogger("webscan.scanner")

# ── Shared thread pool — reused across all requests ──────────────────────────
scanner_executor = ThreadPoolExecutor(max_workers=4)


# ── Scanner directory resolution ─────────────────────────────────────────────
def _get_scanner_dir() -> Path:
    parent = Path(__file__).resolve().parent.parent  # backend/
    candidate = parent / "scanner"
    if candidate.exists():
        return candidate
    fallback = parent.parent / "scanner"
    if fallback.exists():
        return fallback
    raise FileNotFoundError("scanner directory not found")



# ── Node.js scanner runner ───────────────────────────────────────────────────
def run_node_scanner(script_name: str, url: str, timeout: int = 120) -> dict | None:
    """Run a Node.js scanner script and return parsed JSON, or None on failure."""
    try:
        scanner_dir = _get_scanner_dir()
        script_path = scanner_dir / script_name
        if not script_path.exists():
            logger.warning("Scanner script not found: %s", script_name)
            return None
        proc = subprocess.run(
            ["node", str(script_path), url],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(scanner_dir),
        )
        if proc.returncode != 0:
            logger.warning(
                "Scanner %s failed (exit %d): %s",
                script_name, proc.returncode, proc.stderr[:200],
            )
            return None
        return json.loads(proc.stdout.strip())
    except subprocess.TimeoutExpired:
        logger.warning("Scanner %s timed out after %ds", script_name, timeout)
        return None
    except json.JSONDecodeError as e:
        logger.warning("Scanner %s returned invalid JSON: %s", script_name, e)
        return None
    except Exception as e:
        logger.warning("Scanner %s unexpected error: %s", script_name, e)
        return None


def run_single_scanner(script_name: str, url: str, timeout: int = 120) -> dict:
    """Run a single scanner with full error reporting (for individual endpoints)."""
    scanner_dir = _get_scanner_dir()
    script_path = scanner_dir / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"{script_name} not found")

    try:
        proc = subprocess.run(
            ["node", str(script_path), url],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(scanner_dir),
        )
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"{script_name} timed out (>{timeout}s)")

    raw_output = proc.stdout.strip()
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError:
        detail = f"Unexpected output: {raw_output[:300]}"
        if proc.stderr:
            detail += f" | stderr: {proc.stderr[:200]}"
        raise ValueError(detail)

    if proc.returncode != 0:
        raise RuntimeError(data.get("error", f"Scanner failed: {raw_output[:300]}"))

    return data


# ── Common admin paths for fast probing (shared with standards evaluators) ────
from services.standards.helpers import ADMIN_PATHS as ADMIN_PROBE_PATHS

# ── XSS / SQLi active-scan rule IDs in ZAP ──────────────────────────────────
# These are the only rules we need for NCSA checks (ncsa-07: XSS & SQL Injection)
_XSS_SQLI_SCANNER_IDS = [
    "40012",  # Cross Site Scripting (Reflected)
    "40014",  # Cross Site Scripting (Persistent) - Spider
    "40016",  # Cross Site Scripting (Persistent) - Attack
    "40018",  # SQL Injection
    "40019",  # SQL Injection - MySQL
    "40020",  # SQL Injection - Hypersonic
    "40021",  # SQL Injection - Oracle
    "40022",  # SQL Injection - PostgreSQL
    "40024",  # SQL Injection - SQLite
    "40026",  # Cross Site Scripting (DOM Based)
    "90018",  # Advanced SQL Injection
]


async def _probe_admin_urls(url: str) -> list[dict]:
    """Fast parallel HTTP probe for common admin/login paths.
    Returns list of ZAP-compatible alert dicts for found admin URLs."""
    from urllib.parse import urlparse, urljoin
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    found_alerts = []
    async with httpx.AsyncClient(
        timeout=8.0,
        follow_redirects=True,
        headers={"User-Agent": "WebScan-AdminProbe/1.0"},
    ) as client:
        async def _check(path: str):
            try:
                target = urljoin(base, path)
                resp = await client.get(target)
                # Consider it "found" if returns 200 or 401/403 (auth-protected)
                if resp.status_code in (200, 401, 403):
                    return {
                        "alert": f"Exposed Admin/Login URL: {path}",
                        "risk": "Low",
                        "url": target,
                        "param": "",
                        "evidence": f"HTTP {resp.status_code}",
                        "description": f"Admin/login path {path} is accessible (HTTP {resp.status_code})",
                        "sourceid": "admin-probe",
                    }
            except Exception:
                pass
            return None

        results = await asyncio.gather(*[_check(p) for p in ADMIN_PROBE_PATHS])
        found_alerts = [r for r in results if r is not None]

    return found_alerts


# ── ZAP scanner (optimized) ──────────────────────────────────────────────────
async def run_zap_scan(url: str) -> dict | None:
    """Run optimized ZAP spider + targeted active scan.

    Optimizations vs. the original:
      - Spider: maxDepth=1, maxChildren=10, maxDuration=15s
      - Active scan: only XSS & SQLi rules, recurse=false
      - Admin URL detection: fast parallel HTTP probes (no ZAP dependency)
      - Reduced poll intervals

    Typical scan time: 20-40 seconds (vs. 5-7 minutes originally).
    """
    import time
    t0 = time.monotonic()
    params = {"apikey": ZAP_API_KEY}

    try:
        async with httpx.AsyncClient(base_url=ZAP_BASE_URL, timeout=30.0) as client:
            # ── 0. Check ZAP reachability ────────────────────────────────
            try:
                await client.get(
                    "/JSON/core/action/accessUrl/",
                    params={**params, "url": url, "followRedirects": "true"},
                )
            except httpx.RequestError:
                logger.warning("ZAP not reachable at %s", ZAP_BASE_URL)
                return None

            # ── 1. Spider (shallow — depth 1, max 10 children, 15s cap) ──
            spider_params = {
                **params,
                "url": url,
                "maxChildren": "10",
                "recurse": "true",
                "subtreeOnly": "true",
            }
            resp = await client.get(
                "/JSON/spider/action/scan/", params=spider_params,
            )
            spider_id = resp.json().get("scan")
            if spider_id is None:
                logger.warning("ZAP spider failed to start")
                return None

            logger.info("ZAP spider %s started for %s", spider_id, url)

            # Poll spider — max 20s (10 iterations × 2s)
            for i in range(10):
                resp = await client.get(
                    "/JSON/spider/view/status/",
                    params={**params, "scanId": spider_id},
                )
                status = int(resp.json().get("status", "0"))
                if status >= 100:
                    break
                await asyncio.sleep(2)
            else:
                # Force-stop spider if still running after 20s
                try:
                    await client.get(
                        "/JSON/spider/action/stop/",
                        params={**params, "scanId": spider_id},
                    )
                    logger.info("ZAP spider %s force-stopped after 20s", spider_id)
                except Exception:
                    pass

            t_spider = time.monotonic() - t0
            logger.info("ZAP spider completed in %.1fs", t_spider)

            # ── 2. Active scan (targeted — XSS/SQLi only, no recurse) ────
            # Attempt to disable irrelevant scanners and enable only XSS/SQLi rules
            try:
                await client.get("/JSON/ascan/action/disableAllScanners/", params=params)
                await client.get(
                    "/JSON/ascan/action/enableScanners/",
                    params={**params, "ids": ",".join(_XSS_SQLI_SCANNER_IDS)},
                )
            except Exception as e:
                logger.debug("Could not filter ZAP scanners: %s", e)

            ascan_params = {
                **params,
                "url": url,
                "recurse": "false",           # Only scan the target URL, not children
                "scanPolicyName": "",          # Default policy (scanners configured above)
            }
            resp = await client.get(
                "/JSON/ascan/action/scan/", params=ascan_params,
            )
            ascan_id = resp.json().get("scan")
            if ascan_id is None:
                logger.warning("ZAP active scan failed to start")
                # Still return spider results + admin probe
            else:
                logger.info("ZAP active scan %s started (XSS/SQLi only, no recurse)", ascan_id)

                # Poll active scan — max 60s (30 iterations × 2s)
                for i in range(30):
                    resp = await client.get(
                        "/JSON/ascan/view/status/",
                        params={**params, "scanId": ascan_id},
                    )
                    status = int(resp.json().get("status", "0"))
                    if status >= 100:
                        break
                    await asyncio.sleep(2)
                else:
                    # Force-stop active scan if still running after 60s
                    try:
                        await client.get(
                            "/JSON/ascan/action/stop/",
                            params={**params, "scanId": ascan_id},
                        )
                        logger.info("ZAP active scan %s force-stopped after 60s", ascan_id)
                    except Exception:
                        pass

            t_ascan = time.monotonic() - t0
            logger.info("ZAP active scan completed in %.1fs total", t_ascan)

            # ── 3. Collect ZAP alerts ────────────────────────────────────
            resp = await client.get(
                "/JSON/alert/view/alerts/", params={**params, "baseurl": url}
            )
            alerts = resp.json().get("alerts", [])

        # ── 4. Fast admin URL probe (parallel, independent of ZAP) ───
        admin_alerts = await _probe_admin_urls(url)
        all_alerts = alerts + admin_alerts

        risk_summary = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
        for alert in all_alerts:
            risk = alert.get("risk", "Informational")
            risk_summary[risk] = risk_summary.get(risk, 0) + 1

        total_time = time.monotonic() - t0
        logger.info(
            "ZAP scan complete for %s — %d alerts in %.1fs (spider: %.1fs, total: %.1fs)",
            url, len(all_alerts), total_time, t_spider, total_time,
        )

        return {
            "url": url,
            "total_alerts": len(all_alerts),
            "risk_summary": risk_summary,
            "alerts": all_alerts,
            "scan_time_seconds": round(total_time, 1),
        }
    except Exception as e:
        logger.warning("ZAP scan failed: %s", e)
        return None
