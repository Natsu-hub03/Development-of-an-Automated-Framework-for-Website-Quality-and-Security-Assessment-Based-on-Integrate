"""
AI Analysis endpoints:
- POST /analyze/ai: High-accuracy, grounded security analysis & report generation.
- POST /analyze/ai-fix: Actionable step-by-step code fixes for specific checklist items.
- POST /analyze/ai-batch: Batch-analyze multiple checklist items for dashboard integration.
"""
import json
import logging
from typing import Any, Optional, Dict, List

import ollama
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

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


def extract_grounded_scan_facts(scan_data: Any, max_chars: int = 3500) -> str:
    """
    Extract factual findings cleanly from scan_data without breaking JSON or overflowing context.
    Prevents hallucination by feeding structured, unambiguous facts to the model.
    """
    if isinstance(scan_data, dict):
        data = scan_data.get("data", scan_data) if isinstance(scan_data.get("data"), dict) else scan_data

        lines: List[str] = []

        # 1. Summary Counts
        summary = data.get("summary")
        if isinstance(summary, dict):
            lines.append(
                f"📊 สรุปผลการตรวจสอบ: ทั้งหมด {summary.get('total', 0)} รายการ "
                f"| ผ่าน: {summary.get('passed', 0)} "
                f"| ไม่ผ่าน: {summary.get('failed', 0)} "
                f"| เฝ้าระวัง: {summary.get('warning', 0)}"
            )

        # 2. Detected Technologies
        techs = data.get("wappalyzer_technologies") or data.get("technologies") or []
        if isinstance(techs, list) and techs:
            tech_items = []
            for t in techs:
                if isinstance(t, dict):
                    name = t.get("name", "")
                    ver = t.get("version")
                    tech_items.append(f"{name} (v{ver})" if ver else name)
                elif isinstance(t, str):
                    tech_items.append(t)
            if tech_items:
                lines.append(f"🛠️ เทคโนโลยีและไลบรารีที่ตรวจพบ: {', '.join(tech_items)}")

        # 3. Failed & Warning Checklist Items
        standards = data.get("standards")
        if isinstance(standards, list):
            failed_items: List[str] = []
            warning_items: List[str] = []
            passed_items: List[str] = []

            for std in standards:
                if not isinstance(std, dict):
                    continue
                std_name = std.get("name", "Standard")
                for cat in std.get("categories", []):
                    if not isinstance(cat, dict):
                        continue
                    for check in cat.get("checks", []):
                        if not isinstance(check, dict):
                            continue
                        status = check.get("status")
                        chk_name = check.get("name_th") or check.get("name") or check.get("id")
                        detail = check.get("detail", "").strip()

                        if status == "fail":
                            detail_str = f" - สาเหตุ: {detail}" if detail else ""
                            failed_items.append(f"[{std_name}] ❌ {chk_name}{detail_str}")
                        elif status == "warning":
                            detail_str = f" - ข้อสังเกต: {detail}" if detail else ""
                            warning_items.append(f"[{std_name}] ⚠️ {chk_name}{detail_str}")
                        elif status == "pass":
                            passed_items.append(f"[{std_name}] ✅ {chk_name}")

            if failed_items:
                lines.append("\n❌ รายการที่ไม่ผ่านการทดสอบ (Failed Checks):")
                lines.extend(f"  • {item}" for item in failed_items)

            if warning_items:
                lines.append("\n⚠️ รายการที่พบข้อสังเกต/ควรเฝ้าระวัง (Warnings):")
                lines.extend(f"  • {item}" for item in warning_items)

        # 4. Direct ZAP Alerts (if raw zap data passed)
        zap_alerts = data.get("alerts") or data.get("zap_alerts")
        if isinstance(zap_alerts, list) and zap_alerts:
            lines.append("\n🛡️ ช่องโหว่ที่ ZAP ตรวจพบ (ZAP Alerts):")
            for alert in zap_alerts[:10]:
                if isinstance(alert, dict):
                    risk = alert.get("risk", "Info")
                    name = alert.get("alert", alert.get("name", "Alert"))
                    lines.append(f"  • [{risk}] {name}")

        if lines:
            text = "\n".join(lines)
            if len(text) > max_chars:
                return text[:max_chars] + "\n...(ข้อมูลส่วนที่เหลือถูกตัดเนื่องจากขนาดยาวเกินกำหนด)"
            return text

    # Fallback to safely truncated json
    try:
        raw_json = json.dumps(scan_data, ensure_ascii=False, indent=2)
        if len(raw_json) > max_chars:
            return raw_json[:max_chars] + "\n... (truncated)"
        return raw_json
    except Exception:
        return str(scan_data)[:max_chars]


@router.post("/analyze/ai")
async def analyze_with_ai(
    request: AIAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Send structured scan results to Ollama (local LLM) for grounded, factual security analysis.
    Returns a markdown report strictly based on observed findings.
    """
    grounded_data = extract_grounded_scan_facts(request.scan_data, max_chars=MAX_JSON_CHARS)

    prompt = f"""คุณเป็นผู้เชี่ยวชาญอาวุโสด้าน Cybersecurity และ Web Application Security ที่มีใบรับรอง OSCP, CISSP
เชี่ยวชาญ OWASP Top 10, CWE/CVE taxonomy, NIST Cybersecurity Framework และมาตรฐานความปลอดภัย สกมช.

กรุณาวิเคราะห์ผลการตรวจสอบเว็บไซต์ต่อไปนี้อย่างแม่นยำและเป็นกลาง:
- URL เป้าหมาย: {request.url}
- ประเภทการสแกน: {request.scan_type}

ข้อมูลผลการตรวจสอบจริง (Scan Data):
{grounded_data}

กฎสำคัญสำหรับการวิเคราะห์ (Strict Factual Grounding Rules):
1. ยึดตาม "ข้อมูลผลการตรวจสอบจริงข้างต้นเท่านั้น" ห้ามกุขึ้นมาเองหรือคาดเดาช่องโหว่ที่ไม่มีในผลสแกน (ห้าม Hallucinate เช่น ห้ามอ้างว่ามี SQL Injection, XSS, หรือ RCE หากผลสแกนไม่ได้ระบุว่าตรวจพบ)
2. หากเทคโนโลยีใดไม่มีการระบุเวอร์ชัน ให้ระบุว่า "ไม่ระบุเวอร์ชัน" ห้ามเดาเวอร์ชันหรือเดาหมายเลข CVE
3. ประเมินระดับความเสี่ยง (Risk Score 1-10) ให้สอดคล้องกับจำนวนและความรุนแรงของรายการที่ไม่ผ่านจริง
4. เขียนเนื้อหาเป็นภาษาไทยที่กระชับ ชัดเจน เข้าใจง่าย คงคำศัพท์เทคนิคเป็นภาษาอังกฤษตามมาตรฐาน

กรุณาจัดรูปแบบรายงานเป็น Markdown ตามโครงสร้างดังนี้:
### 1. 📋 บทสรุปสำหรับผู้บริหาร (Executive Summary)
(สรุปภาพรวมสถานะความปลอดภัยของเว็บไซต์ 2-3 ประโยค จากผลการตรวจจริง)

### 2. 🛠️ เทคโนโลยีที่ตรวจพบและความเสี่ยงที่เกี่ยวข้อง (Detected Technologies)
(วิเคราะห์เทคโนโลยีที่พบและข้อควรระวังตามผลสแกน)

### 3. ⚠️ ปัญหาและความเสี่ยงด้านความปลอดภัยที่ตรวจพบ (Identified Security Issues)
(ระบุรายการปัญหาที่ 'ไม่ผ่าน' หรือ 'เตือน' พร้อมระดับความเสี่ยง Risk Level, ผลกระทบ Impact, และแนวทางแก้ไข)

### 4. 🎯 5 คำแนะนำสำคัญเร่งด่วน (Top 5 Actionable Recommendations)
(ข้อเสนอแนะ 5 ข้อที่เป็นรูปธรรมและแก้ไขปัญหาที่ตรวจพบข้างต้นได้ตรงจุด อ้างอิงตาม OWASP / NIST)

### 5. 📊 ระดับความเสี่ยงโดยรวม (Overall Risk Score)
(ให้คะแนน 1-10 พร้อมเหตุผลประกอบที่อิงจากรายการที่ไม่ผ่าน)
"""

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_ctx": 4096,
                "num_predict": 1024,
                "temperature": 0.15,  # Low temperature for deterministic, factual output
                "top_p": 0.9,
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
    Generate accurate, actionable step-by-step fix recommendations in Thai for a specific checklist item.
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

กรุณาวิเคราะห์และให้คำแนะนำวิธีแก้ไขสำหรับรายการตรวจสอบต่อไปนี้โดยอิงตามข้อเท็จจริงและมาตรฐานสากล:
- รหัสตรวจสอบ: {request.check_id}
- ชื่อรายการ: {request.check_name} ({request.check_name_th or ''})
- สถานะปัจจุบัน: {request.status}
- ปัญหาที่ตรวจพบ: {request.detail}
- ความสำคัญ/เหตุผล: {request.why_th or 'ตามมาตรฐาน'}
- ข้อมูลหลักฐานโค้ดที่พบ (Evidence):
{evidence_str or 'ไม่มีข้อมูล snippet เฉพาะจุด'}

กฎการตอบ:
1. ตอบตรงประเด็น ให้คำแนะนำที่ถูกต้องและใช้แก้ไขได้จริงตามมาตรฐาน
2. ห้ามแต่งเติมข้อมูลที่ไม่มีอยู่จริง
3. ให้ตัวอย่างโค้ดที่ถูกต้องและปลอดภัย

กรุณาตอบเป็นภาษาไทยแบบกระชับ ชัดเจน และจัดรูปแบบ Markdown ดังนี้:
1. 🔍 **สาเหตุของปัญหา**: สรุปสั้นๆ 1-2 ประโยคว่าทำไมถึงไม่ผ่าน
2. 💡 **วิธีแก้ไขทีละขั้นตอน (Step-by-step)**: ข้อ 1, 2, 3 ชัดเจนและนำไปทำตามได้ทันที
3. 💻 **ตัวอย่างโค้ดที่ถูกต้อง**: ยกตัวอย่างโค้ด HTML / CSS / Nginx config หรือ JS ที่แก้ไขแล้วพร้อมคำอธิบายสั้นๆ
4. 🛡️ **คำแนะนำเสริมด้านความปลอดภัย**: ข้อควรระวังเพิ่มเติมตามมาตรฐาน
"""

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_ctx": 4096,
                "num_predict": 1024,
                "temperature": 0.15,  # Deterministic fix suggestions
                "top_p": 0.9,
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
                    "temperature": 0.2,
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
