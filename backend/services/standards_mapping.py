"""
Backward compatibility proxy module.
All logic has been modularized into the `services.standards` package.
"""

from services.standards import (
    build_standards_report,
    build_single_standard_report,
    CHECKS,
    STANDARDS_META,
    STANDARD_TOOLS,
    VALID_STANDARD_IDS,
    PASS,
    FAIL,
    WARNING,
    ADMIN_PATHS,
    _extract,
    evaluate_one,
)
from services.standards.helpers import (
    INFO,
    WEAK_CIPHERS,
    _make,
)
from services.standards.evaluators import (
    _eval_axe,
    _eval_lh,
    _eval_header,
    _eval_server_info,
    _eval_tls_version,
    _eval_cipher,
    _eval_xss_sqli,
    _eval_cookie_security,
    _eval_fingerprinting,
    _eval_cve,
    _eval_admin_urls,
    _eval_set_cookie_owasp,
    _eval_xxss_deprecated,
)

__all__ = [
    "build_standards_report",
    "build_single_standard_report",
    "CHECKS",
    "STANDARDS_META",
    "STANDARD_TOOLS",
    "VALID_STANDARD_IDS",
    "PASS",
    "FAIL",
    "WARNING",
    "INFO",
    "ADMIN_PATHS",
    "WEAK_CIPHERS",
    "_extract",
    "_make",
    "evaluate_one",
]
