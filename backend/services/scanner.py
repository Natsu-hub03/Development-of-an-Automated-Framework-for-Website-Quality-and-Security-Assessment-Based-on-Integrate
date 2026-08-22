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


def _get_scanner_path() -> Path:
    return _get_scanner_dir() / "wappalyzer_scan.js"


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


# ── ZAP scanner ──────────────────────────────────────────────────────────────
async def run_zap_scan(url: str) -> dict | None:
    """Run ZAP spider + active scan. Returns result dict or None."""
    params = {"apikey": ZAP_API_KEY}
    try:
        async with httpx.AsyncClient(base_url=ZAP_BASE_URL, timeout=30.0) as client:
            # Access URL
            try:
                await client.get(
                    "/JSON/core/action/accessUrl/",
                    params={**params, "url": url, "followRedirects": "true"},
                )
            except httpx.RequestError:
                logger.warning("ZAP not reachable at %s", ZAP_BASE_URL)
                return None

            # Spider
            resp = await client.get(
                "/JSON/spider/action/scan/", params={**params, "url": url}
            )
            spider_id = resp.json().get("scan")
            if spider_id is None:
                logger.warning("ZAP spider failed to start")
                return None

            for _ in range(60):
                resp = await client.get(
                    "/JSON/spider/view/status/",
                    params={**params, "scanId": spider_id},
                )
                if int(resp.json().get("status", "0")) >= 100:
                    break
                await asyncio.sleep(2)

            # Active scan
            resp = await client.get(
                "/JSON/ascan/action/scan/", params={**params, "url": url}
            )
            ascan_id = resp.json().get("scan")
            if ascan_id is None:
                logger.warning("ZAP active scan failed to start")
                return None

            for _ in range(100):
                resp = await client.get(
                    "/JSON/ascan/view/status/",
                    params={**params, "scanId": ascan_id},
                )
                if int(resp.json().get("status", "0")) >= 100:
                    break
                await asyncio.sleep(3)

            # Alerts
            resp = await client.get(
                "/JSON/alert/view/alerts/", params={**params, "baseurl": url}
            )
            alerts = resp.json().get("alerts", [])

            risk_summary = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
            for alert in alerts:
                risk = alert.get("risk", "Informational")
                risk_summary[risk] = risk_summary.get(risk, 0) + 1

            return {
                "url": url,
                "total_alerts": len(alerts),
                "risk_summary": risk_summary,
                "alerts": alerts,
            }
    except Exception as e:
        logger.warning("ZAP scan failed: %s", e)
        return None
