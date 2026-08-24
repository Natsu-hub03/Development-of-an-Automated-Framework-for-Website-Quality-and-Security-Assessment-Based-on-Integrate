"""
Shared Pydantic models for API endpoints.
"""

from pydantic import BaseModel, AnyHttpUrl


class ScanRequest(BaseModel):
    """Common request body for scan endpoints."""
    url: AnyHttpUrl
