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
from typing import Any, Optional

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_JSON_CHARS
from db.database import get_db
from db.models import Scan, AIReport

logger = logging.getLogger("webscan.routes.ai")
router = APIRouter(tags=["ai"])


class AIAnalyzeRequest(BaseModel):
    url: str
    scan_data: Any
    scan_type: str = "both"


class CheckAIFixRequest(BaseModel):
    check_id: str
    check_name: str
    check_name_th: Optional[str] = None
    status: str
    detail: str
    why_th: Optional[str] = None
    evidence: Optional[Any] = None


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


@router.post("/analyze/ai-fix")
async def analyze_check_fix_with_ai(request: CheckAIFixRequest):
    """
    Generate actionable step-by-step fix recommendations in Thai for a specific checklist item.
    """
    evidence_str = ""
    if request.evidence:
        try:
            evidence_str = json.dumps(request.evidence, ensure_ascii=False, indent=2)[:1500]
        except Exception:
            evidence_str = str(request.evidence)[:1500]

    prompt = f"""คุณเป็นผู้เชี่ยวชาญระดับ Senior ด้าน Web Accessibility (WCAG 2.1), Web Performance (Core Web Vitals), และ Web Security (OWASP & มาตรฐาน สกมช.)

กรุณาวิเคราะห์และให้คำแนะนำวิธีแก้ไขสำหรับรายการตรวจสอบต่อไปนี้:
- รหัสตรวจสอบ: {request.check_id}
- ชื่อรายการ: {request.check_name} ({request.check_name_th or ''})
- สถานะปัจจุบัน: {request.status}
- ปัญหาที่ตรวจพบ: {request.detail}
- ความสำคัญ/เหตุผล: {request.why_th or 'ตามมาตรฐาน'}
- ข้อมูลหลักฐานโค้ดที่พบ (Evidence):
{evidence_str or 'ไม่มีข้อมูล snippet เฉพาะจุด'}

กรุณาตอบเป็นภาษาไทยแบบกระชับ ชัดเจน เข้าใจง่าย และตรงประเด็น โดยจัดรูปแบบ Markdown ดังนี้:
1. 🔍 **สาเหตุของปัญหา**: สรุปสั้นๆ ว่าทำไมถึงไม่ผ่าน
2. 💡 **วิธีแก้ไขทีละขั้นตอน (Step-by-step)**: ข้อ 1, 2, 3 สั้นกระชับ
3. 💻 **ตัวอย่างโค้ดที่ถูกต้อง**: ยกตัวอย่างโค้ด HTML / CSS / Nginx config หรือ JS ที่แก้ไขเสร็จแล้ว
"""

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_ctx": 4096,
                "num_predict": 1024,
                "temperature": 0.5,
            },
        )
        return {
            "success": True,
            "check_id": request.check_id,
            "ai_advice": response.response,
        }
    except ollama.ResponseError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama error: {e.error}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not reachable: {str(e)}"
        )
