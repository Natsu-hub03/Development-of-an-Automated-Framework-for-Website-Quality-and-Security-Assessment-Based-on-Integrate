"""
AI Analysis endpoint: POST /analyze/ai

Sends scan results to Ollama (local LLM) for security analysis.
Persists the AI report to Postgres for later retrieval.
"""
import json
import logging

import ollama
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Any

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_JSON_CHARS
from db.database import get_db
from db.models import Scan, AIReport

logger = logging.getLogger("webscan.routes.ai")
router = APIRouter(tags=["ai"])


class AIAnalyzeRequest(BaseModel):
    url: str
    scan_data: Any
    scan_type: str = "both"


@router.post("/analyze/ai")
async def analyze_with_ai(
    request: AIAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Send scan results to Ollama (local LLM) for security analysis.
    Returns a structured markdown report and persists it to the database.
    """
    # Build prompt — truncate scan data to avoid context overflow on small models
    scan_json = json.dumps(request.scan_data, ensure_ascii=False, indent=2)
    if len(scan_json) > MAX_JSON_CHARS:
        scan_json = scan_json[:MAX_JSON_CHARS] + "\n... (truncated)"

    prompt = f"""You are an expert web application security analyst.

Analyze the following scan results for the website: {request.url}
Scan type: {request.scan_type}

Scan data:
{scan_json}

Provide a security analysis report in markdown with these sections:
1. Executive Summary (2-3 sentences)
2. Detected Technologies and security implications
3. Vulnerabilities and Risks (Risk Level, Issue, Impact, Recommendation)
4. Top 5 Security Recommendations
5. Overall Risk Score 1-10 with justification

Use Thai for descriptions, keep technical terms in English.
"""

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_ctx": 4096,
                "num_predict": 1024,
                "temperature": 0.7,
            },
        )
        analysis_text = response.response
    except ollama.ResponseError as e:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama model error: {e.error}. "
                f"Make sure model '{OLLAMA_MODEL}' is pulled: "
                f"`ollama pull {OLLAMA_MODEL}`"
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Ollama not reachable at {OLLAMA_BASE_URL}. "
                f"Install from https://ollama.com and run: "
                f"ollama pull {OLLAMA_MODEL}"
            ),
        )

    # Persist AI report to database
    try:
        # Find the most recent scan for this URL to link to
        recent_scan = (
            db.query(Scan)
            .filter(Scan.url == request.url)
            .order_by(Scan.created_at.desc())
            .first()
        )

        if recent_scan:
            ai_report = AIReport(
                scan_id=recent_scan.id,
                url=request.url,
                model_name=OLLAMA_MODEL,
                analysis_text=analysis_text,
            )
            db.add(ai_report)
            db.commit()
            logger.info(
                "AI report saved for scan_id=%d, url=%s",
                recent_scan.id, request.url,
            )
    except Exception as e:
        db.rollback()
        logger.warning("Failed to persist AI report: %s", e)
        # Don't fail the request — the analysis was generated successfully

    return {
        "success": True,
        "url": request.url,
        "model": OLLAMA_MODEL,
        "analysis": analysis_text,
    }
