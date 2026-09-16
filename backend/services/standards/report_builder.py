"""
Report builder — assembles individual check evaluations into the
structured standards compliance report.
"""

from datetime import datetime, timezone
from typing import Any

from services.standards.helpers import _extract, PASS, FAIL, WARNING
from services.standards.checks import CHECKS, STANDARDS_META
from services.standards.evaluators import evaluate_one


# ══════════════════════════════════════════════════════════════════════════════
#  Internal: group results into standard → category hierarchy
# ══════════════════════════════════════════════════════════════════════════════

def _build_standards_list(results: list[dict], standard_ids: list[str] | None = None):
    """Group evaluated results into standard → category structure.
    If standard_ids is given, only include those standards."""
    standards = []
    for meta in STANDARDS_META:
        std_id = meta["id"]
        if standard_ids and std_id not in standard_ids:
            continue
        std_checks = [r for r in results if r["standard"] == std_id]

        seen_cats: list[str] = []
        cat_map: dict[str, list] = {}
        for c in std_checks:
            cat = c["category"]
            if cat not in cat_map:
                seen_cats.append(cat)
                cat_map[cat] = []
            item = {
                "id": c["id"],
                "name": c["name"],
                "name_th": c["name_th"],
                "why_th": c.get("why_th", ""),
                "remediation_th": c.get("remediation_th", ""),
                "status": c["status"],
                "detail": c["detail"],
                "source_tool": c["source_tool"],
            }
            if c.get("evidence"):
                item["evidence"] = c["evidence"]
            if c.get("evidence_type"):
                item["evidence_type"] = c["evidence_type"]
            cat_map[cat].append(item)

        categories = [
            {"name": cat, "checks": cat_map[cat]}
            for cat in seen_cats
        ]

        p = sum(1 for c in std_checks if c["status"] == PASS)
        f = sum(1 for c in std_checks if c["status"] == FAIL)
        w = sum(1 for c in std_checks if c["status"] == WARNING)

        standards.append({
            **meta,
            "total": len(std_checks),
            "passed": p,
            "failed": f,
            "warning": w,
            "categories": categories,
        })
    return standards


# ══════════════════════════════════════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════════════════════════════════════

def build_standards_report(
    url: str,
    axe_data: Any = None,
    lighthouse_data: Any = None,
    headers_data: Any = None,
    wappalyzer_data: Any = None,
    zap_data: Any = None,
) -> dict:
    """Build the complete standards compliance report."""

    # Normalize — unwrap API response envelopes
    axe = _extract(axe_data)
    lh = _extract(lighthouse_data)
    hdr = _extract(headers_data)
    wap = _extract(wappalyzer_data)
    zap = _extract(zap_data)

    # Evaluate every check
    results = [evaluate_one(c, axe, lh, hdr, wap, zap) for c in CHECKS]

    # Group by standard → category (preserving order from CHECKS)
    standards = _build_standards_list(results)

    total_p = sum(s["passed"] for s in standards)
    total_f = sum(s["failed"] for s in standards)
    total_w = sum(s["warning"] for s in standards)

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(CHECKS),
            "passed": total_p,
            "failed": total_f,
            "warning": total_w,
        },
        "standards": standards,
    }


def build_single_standard_report(
    standard_id: str,
    url: str,
    axe_data: Any = None,
    lighthouse_data: Any = None,
    headers_data: Any = None,
    wappalyzer_data: Any = None,
    zap_data: Any = None,
) -> dict:
    """Build a standards compliance report for a single standard only."""

    # Normalize
    axe = _extract(axe_data)
    lh = _extract(lighthouse_data)
    hdr = _extract(headers_data)
    wap = _extract(wappalyzer_data)
    zap = _extract(zap_data)

    # Only evaluate checks for this standard
    filtered_checks = [c for c in CHECKS if c["standard"] == standard_id]
    results = [evaluate_one(c, axe, lh, hdr, wap, zap) for c in filtered_checks]

    standards = _build_standards_list(results, [standard_id])

    total_p = sum(s["passed"] for s in standards)
    total_f = sum(s["failed"] for s in standards)
    total_w = sum(s["warning"] for s in standards)
    total_items = sum(s["total"] for s in standards)

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": total_items,
            "passed": total_p,
            "failed": total_f,
            "warning": total_w,
        },
        "standards": standards,
    }
