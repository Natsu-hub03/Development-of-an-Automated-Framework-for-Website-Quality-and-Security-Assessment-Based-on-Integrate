"""
Shared helper functions and status constants for the standards evaluation system.
"""

from typing import Any, Optional
from standards_guidance import get_guidance


# ── Status constants ──────────────────────────────────────────────────────────
PASS = "pass"
FAIL = "fail"
WARNING = "warning"
INFO = "info"

# ── Weak cipher patterns ─────────────────────────────────────────────────────
WEAK_CIPHERS = ["RC4", "DES", "3DES", "NULL", "EXPORT", "RC2", "IDEA", "SEED"]

# ── Common admin paths ───────────────────────────────────────────────────────
ADMIN_PATHS = [
    "/admin", "/wp-admin", "/wp-login.php", "/administrator",
    "/login", "/phpmyadmin", "/cpanel", "/webmail",
    "/manager", "/console", "/dashboard/login",
]


# ══════════════════════════════════════════════════════════════════════════════
#  Helper: extract inner "data" from API response envelope
# ══════════════════════════════════════════════════════════════════════════════
def _extract(raw: Any) -> Optional[dict]:
    """Unwrap {success, scan_id, data: {...}} envelope or return raw dict."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        if raw.get("error"):
            return None
        if "data" in raw and isinstance(raw["data"], dict):
            return raw["data"]
    return raw if isinstance(raw, dict) else None


# ══════════════════════════════════════════════════════════════════════════════
#  Result builder
# ══════════════════════════════════════════════════════════════════════════════
def _make(check: dict, status: str, detail: str, source: str) -> dict:
    guide = get_guidance(check["id"])
    return {
        "id": check["id"],
        "name": check["name"],
        "name_th": check["name_th"],
        "why_th": guide.get("why_th", ""),
        "remediation_th": guide.get("remediation_th", ""),
        "standard": check["standard"],
        "category": check["category"],
        "status": status,
        "detail": detail,
        "source_tool": source,
    }
