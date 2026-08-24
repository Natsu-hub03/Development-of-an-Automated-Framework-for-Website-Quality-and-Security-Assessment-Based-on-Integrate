"""
Standards evaluation package.

Re-exports the public API so consumers can import from
``services.standards`` directly, e.g.::

    from services.standards import build_standards_report, VALID_STANDARD_IDS
"""

from services.standards.report_builder import (
    build_standards_report,
    build_single_standard_report,
)
from services.standards.checks import (
    CHECKS,
    STANDARDS_META,
    STANDARD_TOOLS,
    VALID_STANDARD_IDS,
)
from services.standards.helpers import (
    PASS,
    FAIL,
    WARNING,
    ADMIN_PATHS,
    _extract,
)
from services.standards.evaluators import evaluate_one

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
    "ADMIN_PATHS",
    "_extract",
    "evaluate_one",
]
