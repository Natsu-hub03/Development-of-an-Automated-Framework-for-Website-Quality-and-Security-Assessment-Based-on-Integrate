"""
Unit tests for 71-item standards mapping logic in services/standards/
"""

from services.standards import (
    CHECKS,
    STANDARDS_META,
    PASS,
    FAIL,
    WARNING,
    _extract,
    build_standards_report,
    build_single_standard_report,
)
from services.standards.helpers import INFO
from services.standards.evaluators import (
    _eval_axe,
    _eval_lh,
    _eval_header,
    _eval_server_info,
    _eval_tls_version,
)


def test_checks_count_and_constants():
    """Verify exactly 71 checks are defined and all status constants exist."""
    assert len(CHECKS) == 71
    assert len(STANDARDS_META) == 4
    assert PASS == "pass"
    assert FAIL == "fail"
    assert WARNING == "warning"
    assert INFO == "info"


def test_extract_envelope():
    """Test unwrapping of API response envelopes vs raw dicts."""
    assert _extract(None) is None
    assert _extract({"error": "Failed"}) is None
    assert _extract({"success": True, "data": {"foo": "bar"}}) == {"foo": "bar"}
    assert _extract({"direct": "data"}) == {"direct": "data"}


def test_eval_axe():
    """Test axe evaluation for pass, fail, and missing data."""
    check = {
        "id": "wcag-01",
        "name": "Document Title",
        "name_th": "ตรวจหาแท็ก <title>",
        "standard": "wcag",
        "category": "โครงสร้าง HTML",
        "rules": ["document-title"],
    }
    # No data -> warning
    res_none = _eval_axe(check, None)
    assert res_none["status"] == WARNING

    # Violation -> fail
    res_fail = _eval_axe(check, {"violations": [{"id": "document-title", "help": "Fix title"}]})
    assert res_fail["status"] == FAIL
    assert res_fail["detail"]

    # Incomplete -> warning
    res_warn = _eval_axe(check, {"violations": [], "incomplete": [{"id": "document-title", "help": "Review title"}]})
    assert res_warn["status"] == WARNING

    # Pass
    res_pass = _eval_axe(check, {"violations": [], "incomplete": []})
    assert res_pass["status"] == PASS


def test_eval_lh():
    """Test Lighthouse evaluation."""
    check = {
        "id": "cwv-01",
        "name": "LCP",
        "name_th": "ความเร็วการโหลดองค์ประกอบหลัก",
        "standard": "cwv",
        "category": "Performance",
        "rules": ["largest-contentful-paint"],
    }
    # Missing data
    assert _eval_lh(check, None)["status"] == WARNING

    # Passed audit
    assert _eval_lh(check, {"failed_audits": []})["status"] == PASS

    # Failed audit with low score
    lh_fail = {
        "failed_audits": [
            {"id": "largest-contentful-paint", "title": "LCP slow", "score": 30, "displayValue": "4.5s"}
        ]
    }
    res_fail = _eval_lh(check, lh_fail)
    assert res_fail["status"] == FAIL


def test_eval_header():
    """Test OWASP header check."""
    check = {
        "id": "owasp-04",
        "name": "X-Content-Type-Options",
        "name_th": "ห้ามเบราว์เซอร์เดาประเภทไฟล์",
        "standard": "owasp",
        "category": "HTTP Security Headers",
        "header": "x-content-type-options",
    }
    # Missing headers data
    assert _eval_header(check, None)["status"] == WARNING

    # Header not present
    assert _eval_header(check, {"security_headers": {}})["status"] == FAIL

    # Header present
    res = _eval_header(check, {"security_headers": {"x-content-type-options": "nosniff"}})
    assert res["status"] == PASS


def test_eval_server_info_and_tls_info_status():
    """Verify WARNING constant is used when headers data is missing in custom evaluators."""
    check_si = {
        "id": "ncsa-04",
        "name": "Server Info",
        "name_th": "ซ่อนข้อมูลเซิร์ฟเวอร์",
        "standard": "ncsa",
        "category": "Security Headers",
    }
    res_si = _eval_server_info(check_si, None, None, None)
    assert res_si["status"] == WARNING

    check_tls = {
        "id": "ncsa-05",
        "name": "TLS Version",
        "name_th": "ตรวจเวอร์ชัน TLS",
        "standard": "ncsa",
        "category": "SSL/TLS Certificate",
    }
    res_tls = _eval_tls_version(check_tls, None, None, None)
    assert res_tls["status"] == WARNING


def test_build_standards_report():
    """Verify complete 71-item report generation."""
    report = build_standards_report("https://example.com")
    assert report["url"] == "https://example.com"
    assert report["summary"]["total"] == 71
    assert len(report["standards"]) == 4

    total_checks = sum(s["total"] for s in report["standards"])
    assert total_checks == 71


def test_build_single_standard_report():
    """Verify single standard report generation."""
    wcag_report = build_single_standard_report("wcag", "https://example.com")
    assert wcag_report["summary"]["total"] == 37
    assert len(wcag_report["standards"]) == 1
    assert wcag_report["standards"][0]["id"] == "wcag"
