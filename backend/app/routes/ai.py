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


class BatchCheckItem(BaseModel):
    check_id: str
    check_name: str
    check_name_th: Optional[str] = None
    status: str
    detail: str
    evidence: Optional[Any] = None


class BatchAIFixRequest(BaseModel):
    items: list[BatchCheckItem]


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

    prompt = f"""คุณเป็นผู้เชี่ยวชาญอาวุโสด้าน Cybersecurity ที่มีประสบการณ์กว่า 15 ปี เชี่ยวชาญเฉพาะทาง Web Application Security
มีใบรับรอง OSCP, CISSP, CEH และเป็นผู้ตรวจประเมินตามมาตรฐาน NIST Cybersecurity Framework (CSF), OWASP ASVS และมาตรฐาน สกมช.
คุณวิเคราะห์ช่องโหว่โดยอ้างอิง OWASP Top 10 (2021), CWE/CVE taxonomy, MITRE ATT&CK framework และ CVSS v3.1 scoring

วิเคราะห์ผลสแกนของเว็บไซต์: {request.url}
ประเภทการสแกน: {request.scan_type}

ข้อมูลผลสแกน:
{scan_json}

สร้างรายงานวิเคราะห์ความปลอดภัยในรูปแบบ Markdown ครอบคลุมหัวข้อเหล่านี้:
1. **Executive Summary** (2-3 ประโยค สรุปสถานะความปลอดภัยภาพรวม)
2. **Attack Surface Analysis** — เทคโนโลยีที่ตรวจพบ พร้อมนัยยะด้านความปลอดภัย ระบุ CVE ที่เกี่ยวข้อง (ถ้ามี)
3. **Vulnerability Assessment** — ตารางช่องโหว่: Risk Level (CVSS Score), CWE ID, OWASP Top 10 Category, ผลกระทบ, วิธีแก้ไข
4. **Threat Modeling** — สถานการณ์ภัยคุกคามที่เป็นไปได้ อ้างอิง MITRE ATT&CK Techniques (เช่น T1190 Exploit Public-Facing Application)
5. **Top 5 Security Recommendations** — จัดลำดับตาม Risk Priority พร้อมอ้างอิง NIST CSF Functions (Identify/Protect/Detect/Respond/Recover)
6. **Overall Risk Score** (1-10) พร้อมเหตุผลอ้างอิง CVSS และ Business Impact

ตอบเป็นภาษาไทย คำศัพท์เทคนิค (OWASP, CVE, CWE, MITRE ATT&CK, NIST) ให้คงเป็นภาษาอังกฤษ
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

    # Persist AI report to database — wrap sync DB in executor
    def _persist_ai_report():
        try:
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

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _persist_ai_report)
    except Exception:
        pass  # Don't fail the request — the analysis was generated successfully

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

    prompt = f"""คุณเป็นผู้เชี่ยวชาญอาวุโสด้าน Cybersecurity และ Web Application Security ที่มีใบรับรอง OSCP, CISSP
เชี่ยวชาญ OWASP Top 10, OWASP ASVS, CWE/CVE taxonomy, NIST Cybersecurity Framework
รวมถึงมาตรฐาน WCAG 2.1 (Accessibility), Core Web Vitals (Performance) และมาตรฐาน สกมช. (NCSA Thailand)

กรุณาวิเคราะห์และให้คำแนะนำวิธีแก้ไขสำหรับรายการตรวจสอบต่อไปนี้:
- รหัสตรวจสอบ: {request.check_id}
- ชื่อรายการ: {request.check_name} ({request.check_name_th or ''})
- สถานะปัจจุบัน: {request.status}
- ปัญหาที่ตรวจพบ: {request.detail}
- ความสำคัญ/เหตุผล: {request.why_th or 'ตามมาตรฐาน'}
- ข้อมูลหลักฐานโค้ดที่พบ (Evidence):
{evidence_str or 'ไม่มีข้อมูล snippet เฉพาะจุด'}

กรุณาตอบเป็นภาษาไทยแบบกระชับ ชัดเจน เข้าใจง่าย ตรงประเด็น โดยจัดรูปแบบ Markdown ดังนี้:
1. 🔍 **สาเหตุของปัญหา**: สรุปสั้นๆ ว่าทำไมถึงไม่ผ่าน พร้อมระบุ CWE ID หรือ OWASP Category ที่เกี่ยวข้อง (ถ้าเป็นประเด็นด้าน Security)
2. ⚠️ **ระดับความเสี่ยง**: ระบุ CVSS Score โดยประมาณ และ Attack Vector ที่เป็นไปได้ (ถ้าเป็นประเด็นด้าน Security) หรือผลกระทบต่อ Accessibility/Performance
3. 💡 **วิธีแก้ไขทีละขั้นตอน (Step-by-step)**: ข้อ 1, 2, 3 สั้นกระชับ อ้างอิง Best Practices จาก OWASP, NIST หรือ WCAG
4. 💻 **ตัวอย่างโค้ดที่ถูกต้อง**: ยกตัวอย่างโค้ด HTML / CSS / Nginx config / JS / Security Header ที่แก้ไขเสร็จแล้ว
5. 🛡️ **การป้องกันเชิงลึก (Defense in Depth)**: แนะนำมาตรการเสริมเพิ่มเติม เช่น WAF rules, CSP policy, monitoring
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


@router.post("/analyze/ai-batch")
async def analyze_batch_fix_with_ai(request: BatchAIFixRequest):
    """
    Batch-analyze multiple failed/warning checklist items.
    Processes sequentially through Ollama, returns ai_risk + ai_fix per item.
    """
    if not request.items:
        return {"success": True, "results": {}}

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama not reachable at {OLLAMA_BASE_URL}",
        )

    results: dict[str, dict[str, str]] = {}

    for item in request.items:
        evidence_str = ""
        if item.evidence:
            try:
                evidence_str = json.dumps(item.evidence, ensure_ascii=False, indent=2)[:1500]
            except Exception:
                evidence_str = str(item.evidence)[:1500]

        prompt = f"""คุณเป็นผู้เชี่ยวชาญอาวุโสด้าน Cybersecurity (OSCP/CISSP) เชี่ยวชาญ OWASP Top 10, CWE/CVE, NIST CSF, MITRE ATT&CK
รวมถึง Web Accessibility (WCAG 2.1) และ Web Performance (Core Web Vitals)

วิเคราะห์ผลตรวจสอบนี้ให้กระชับ ตรงประเด็น ตอบจากข้อมูลจริงที่ตรวจพบ โดยอ้างอิงมาตรฐานสากล:
- รหัส: {item.check_id}
- รายการ: {item.check_name} ({item.check_name_th or ''})
- สถานะ: {item.status}
- ปัญหาที่พบ: {item.detail}
- หลักฐาน (Evidence):
{evidence_str or 'ไม่มี evidence เฉพาะจุด'}

ตอบเป็นภาษาไทยเท่านั้น ในรูปแบบนี้เท่านั้น (ไม่ต้องมีหัวข้ออื่น):

⚡ ความเสี่ยง: [อธิบาย 1-3 ประโยค ว่าปัญหานี้ส่งผลกระทบอะไรต่อเว็บไซต์โดยเฉพาะ อ้างอิง CWE ID, OWASP Category หรือ MITRE ATT&CK Technique ที่เกี่ยวข้อง (ถ้าเป็นด้าน Security) พร้อมระบุ Attack Vector ที่เป็นไปได้]

💡 วิธีแก้: [อธิบาย 1-3 ประโยค ตาม Best Practices จาก OWASP/NIST/WCAG ให้ตัวอย่างโค้ดหรือ config สั้นๆ ถ้าเป็นไปได้]"""

        try:
            response = client.generate(
                model=OLLAMA_MODEL,
                prompt=prompt,
                options={
                    "num_ctx": 4096,
                    "num_predict": 512,
                    "temperature": 0.4,
                },
            )
            raw_text = response.response.strip()

            # Parse AI response into risk + fix sections
            ai_risk = ""
            ai_fix = ""

            if "⚡" in raw_text and "💡" in raw_text:
                parts = raw_text.split("💡")
                risk_part = parts[0]
                fix_part = parts[1] if len(parts) > 1 else ""

                # Clean up risk
                ai_risk = risk_part.replace("⚡", "").strip()
                for prefix in ["ความเสี่ยง:", "ความเสี่ยง :"]:
                    if ai_risk.startswith(prefix):
                        ai_risk = ai_risk[len(prefix):].strip()

                # Clean up fix
                ai_fix = fix_part.strip()
                for prefix in ["วิธีแก้:", "วิธีแก้ :", "วิธีแก้ไข:", "วิธีแก้ไข :"]:
                    if ai_fix.startswith(prefix):
                        ai_fix = ai_fix[len(prefix):].strip()
            else:
                # Fallback: use entire response as risk
                ai_risk = raw_text
                ai_fix = ""

            results[item.check_id] = {
                "ai_risk": ai_risk,
                "ai_fix": ai_fix,
            }
            logger.info("AI batch: analyzed %s", item.check_id)

        except Exception as e:
            logger.warning("AI batch: failed for %s: %s", item.check_id, e)
            results[item.check_id] = {
                "ai_risk": "",
                "ai_fix": "",
            }

    return {"success": True, "results": results}
