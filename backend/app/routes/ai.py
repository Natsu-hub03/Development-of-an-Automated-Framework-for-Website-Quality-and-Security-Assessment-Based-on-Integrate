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


try:
    from standards_guidance import GUIDANCE
except ImportError:
    GUIDANCE = {}


class AIAnalyzeRequest(BaseModel):
    url: str
    scan_data: Any
    scan_type: str = "both"
    force_refresh: bool = False


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


def extract_grounded_scan_facts(scan_data: Any, max_chars: int = 4000) -> str:
    """
    Extract structured, categorized security & quality findings from scan_data.
    Grounds the data with domain knowledge from standards_guidance to prevent hallucination
    and eliminate generic AI filler/slop.
    """
    if isinstance(scan_data, dict):
        data = scan_data.get("data", scan_data) if isinstance(scan_data.get("data"), dict) else scan_data

        sections: List[str] = []

        # 1. Summary Metrics
        summary = data.get("summary")
        if isinstance(summary, dict):
            sections.append(
                f"📊 สรุปตัวเลขผลตรวจ: ตรวจทั้งหมด {summary.get('total', 0)} รายการ "
                f"| ผ่าน ✅ {summary.get('passed', 0)} รายการ "
                f"| ไม่ผ่าน ❌ {summary.get('failed', 0)} รายการ "
                f"| ข้อสังเกต/เฝ้าระวัง ⚠️ {summary.get('warning', 0)} รายการ"
            )

        # 2. Detected Tech Stack
        techs = data.get("wappalyzer_technologies") or data.get("technologies") or []
        if isinstance(techs, list) and techs:
            tech_items = []
            for t in techs:
                if isinstance(t, dict):
                    name = t.get("name", "")
                    ver = t.get("version")
                    cats = [c.get("name") if isinstance(c, dict) else str(c) for c in t.get("categories", [])]
                    cat_str = f" ({', '.join(cats)})" if cats else ""
                    tech_items.append(f"{name}{' v' + str(ver) if ver else ''}{cat_str}")
                elif isinstance(t, str):
                    tech_items.append(t)
            if tech_items:
                sections.append(f"🛠️ Tech Stack ที่ตรวจพบ:\n" + "\n".join(f"  • {item}" for item in tech_items))

        # 3. Categorized Failed & Warning Checklist Items
        standards = data.get("standards")
        if isinstance(standards, list):
            sec_items: List[str] = []     # NCSA & OWASP
            perf_items: List[str] = []    # CWV & SEO
            a11y_items: List[str] = []    # WCAG

            for std in standards:
                if not isinstance(std, dict):
                    continue
                std_id = std.get("id", "").lower()
                std_name = std.get("name", "Standard")

                for cat in std.get("categories", []):
                    if not isinstance(cat, dict):
                        continue
                    for check in cat.get("checks", []):
                        if not isinstance(check, dict):
                            continue
                        status = check.get("status")
                        if status not in ("fail", "warning"):
                            continue

                        chk_id = check.get("id", "")
                        chk_name = check.get("name_th") or check.get("name") or chk_id
                        detail = check.get("detail", "").strip()
                        badge = "❌ ไม่ผ่าน" if status == "fail" else "⚠️ เฝ้าระวัง"

                        # Retrieve technical guidance if known
                        guidance_entry = GUIDANCE.get(chk_id, {})
                        why = guidance_entry.get("why_th", "")
                        remedy = guidance_entry.get("remediation_th", "")

                        item_text = f"[{badge}] {chk_name} (ID: {chk_id})"
                        if detail:
                            item_text += f"\n    - ผลตรวจจริง: {detail}"
                        if why:
                            item_text += f"\n    - ผลกระทบ: {why[:120]}..."

                        if std_id in ("ncsa", "owasp") or "security" in std_name.lower() or "owasp" in std_name.lower():
                            sec_items.append(item_text)
                        elif std_id in ("cwv", "seo") or "vital" in std_name.lower() or "performance" in std_name.lower():
                            perf_items.append(item_text)
                        else:
                            a11y_items.append(item_text)

            if sec_items:
                sections.append("\n🛡️ ประเด็นความมั่นคงปลอดภัย & มาตรฐาน (NCSA & OWASP Headers):\n" + "\n".join(f"  • {item}" for item in sec_items))
            if perf_items:
                sections.append("\n⚡ ประเด็นประสิทธิภาพ & SEO (Core Web Vitals & SEO):\n" + "\n".join(f"  • {item}" for item in perf_items))
            if a11y_items:
                sections.append("\n♿ ประเด็นการเข้าถึง & โครงสร้างเว็บ (WCAG 2.1 Accessibility):\n" + "\n".join(f"  • {item}" for item in a11y_items))

        # 4. Direct ZAP Alerts
        zap_alerts = data.get("alerts") or data.get("zap_alerts")
        if isinstance(zap_alerts, list) and zap_alerts:
            alert_lines = []
            for alert in zap_alerts[:10]:
                if isinstance(alert, dict):
                    risk = alert.get("risk", "Info")
                    name = alert.get("alert", alert.get("name", "Alert"))
                    desc = alert.get("description", "")
                    alert_lines.append(f"  • [{risk}] {name}" + (f" - {desc[:80]}..." if desc else ""))
            if alert_lines:
                sections.append("\n🚨 ช่องโหว่จากการทดสอบ Active Scanner (ZAP Alerts):\n" + "\n".join(alert_lines))

        if sections:
            text = "\n\n".join(sections)
            if len(text) > max_chars:
                return text[:max_chars] + "\n...(สรุปข้อมูลส่วนที่เหลือเพื่อรักษาความกระชับ)"
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
    Send structured scan results to Ollama (local LLM) for grounded, high-level security analysis.
    Returns a comprehensive, executive-ready markdown security & compliance report.
    """
    # 1. Check if a recent AI report already exists for this scan/URL
    try:
        recent_scan = (
            db.query(Scan)
            .filter(Scan.url == request.url)
            .order_by(Scan.created_at.desc())
            .first()
        )
        if recent_scan and not request.force_refresh:
            existing_report = (
                db.query(AIReport)
                .filter(AIReport.scan_id == recent_scan.id)
                .order_by(AIReport.created_at.desc())
                .first()
            )
            # Only return cached report if it was complete and not truncated
            if existing_report and existing_report.analysis_text and len(existing_report.analysis_text) > 300 and "### 5." in existing_report.analysis_text:
                logger.info(
                    "Returning cached complete AI report for scan_id=%d, url=%s",
                    recent_scan.id, request.url,
                )
                return {
                    "success": True,
                    "url": request.url,
                    "model": existing_report.model_name,
                    "analysis": existing_report.analysis_text,
                    "cached": True,
                }
    except Exception as e:
        logger.warning("Cache check failed, proceeding with generation: %s", e)

    grounded_data = extract_grounded_scan_facts(request.scan_data, max_chars=MAX_JSON_CHARS)

    prompt = f"""คุณคือ Senior Cybersecurity Principal Consultant & Web Architect (OSCP, CISSP)
เชี่ยวชาญการประเมินความปลอดภัยตาม OWASP Top 10, ประกาศมาตรฐาน สกมช. (NCSA Thailand), Core Web Vitals และ WCAG 2.1

กรุณาวิเคราะห์ผลการตรวจสอบเว็บไซต์ด้านล่างนี้ และสร้างรายงานวิเคราะห์ความปลอดภัยระดับมืออาชีพสำหรับผู้บริหารและทีมวิศวกร:
- เว็บไซต์เป้าหมาย: {request.url}
- ประเภทการตรวจ: {request.scan_type}

ข้อมูลผลการตรวจสแกนจริง (Grounded Scan Data):
{grounded_data}

กฎสำคัญและมาตรฐานคุณภาพการวิเคราะห์ (Strict Professional Rules):
1. **ห้ามตอบกว้างๆ ซ้ำซาก หรือ AI Fluff**: ห้ามเขียนประโยคที่ไม่ให้สาระ เช่น "เทคโนโลยีมีความเสี่ยงด้านซอฟต์แวร์" แต่ให้เจาะจงที่ Attack Vector, ความเสี่ยงเชิงลึก และผลกระทบต่อระบบจริง
2. **สังเคราะห์ความเสี่ยงเชิงโครงสร้าง (Synthesized Analysis)**: จัดกลุ่มสาเหตุรากเหง้า (Root Cause) และผลกระทบ ไม่แจกแจงแบบท่องจำ
3. **ให้ตัวอย่างคอนฟิก/โค้ดที่ถูกต้องและปลอดภัย (Actionable Code/Config)**: ในส่วนคำแนะนำ ให้มีตัวอย่าง Nginx directives, HTML tags, หรือ security config สั้นๆ ที่ทีมงานนำไปใช้งานได้ทันที
4. **เขียนเป็นภาษาไทยระดับมืออาชีพ**: กระชับ ตรงประเด็น คงชื่อเฉพาะทางเทคนิคภาษาอังกฤษ (เช่น Header Names, Frameworks, Protocols)

กรุณาจัดรูปแบบรายงานเป็น Markdown ให้ครบทั้ง 5 หัวข้อดังนี้:

### 1. 📋 บทสรุปสำหรับผู้บริหาร (Executive Summary)
- **ภาพรวมสถานะความปลอดภัย**: (สรุปความพร้อมและความเสี่ยงโดยรวม 2-3 ประโยค)
- **จุดแข็ง**: (สิ่งที่ระบบทำได้ถูกต้องตามมาตรฐาน)
- **ประเด็นความเสี่ยงวิกฤตที่ต้องเร่งจัดการ**: (สรุป 2-3 ช่องโหว่ที่มีความเสี่ยงสูงสุด)

### 2. 🛠️ การวิเคราะห์ Attack Surface ตาม Tech Stack ที่ตรวจพบ
(วิเคราะห์เจาะลึกเฉพาะเทคโนโลยีที่ตรวจพบจริง เช่น Web Server, CMS, Plugins, Library พร้อมชี้ช่องทางที่ผู้โจมตีอาจใช้เจาะระบบและการป้องกัน)

### 3. ⚠️ เจาะลึกประเด็นและช่องโหว่สำคัญ (Key Findings & Impact)
- 🔴 **ด้านความมั่นคงปลอดภัย (Security & Compliance - NCSA/OWASP)**: (วิเคราะห์ผลกระทบจากการขาด Security Headers สำคัญ เช่น HSTS/CSP/X-Frame-Options, หน้าจัดการระบบที่เปิดสู่สาธารณะ หรือช่องโหว่ซอฟต์แวร์)
- 🟡 **ด้านประสิทธิภาพและ SEO (Core Web Vitals & SEO)**: (วิเคราะห์ปัญหา LCP/TBT ที่สูงผิดปกติ และผลกระทบต่อ Conversion และ Google Ranking)
- 🔵 **ด้านการเข้าถึงและความถูกต้อง (Accessibility - WCAG 2.1)**: (สรุปจุดบกพร่องด้าน Accessibility เช่น Contrast, Alt text, Heading Hierarchy)

### 4. 🎯 5 มาตรการแก้ไขเร่งด่วนพร้อมตัวอย่าง Config (Top 5 Actionable Fixes)
(ระบุ 5 ลำดับความสำคัญเร่งด่วน พร้อมคำอธิบายและ Code / Config Snippet สั้นๆ ที่ถูกต้อง)

### 5. 📊 ระดับความเสี่ยงโดยรวม (Overall Risk Assessment)
- **คะแนนความเสี่ยง (Overall Risk Score)**: [ระบุตัวเลข 1-10 พร้อมระบุระดับ เช่น 6.5/10 - ระดับปานกลางค่อนไปทางสูง]
- **เหตุผลประกอบ**: (สรุปเหตุผลสั้นๆ 2 ประโยครองรับคะแนนความเสี่ยงตามหลักฐานที่ตรวจพบ)
"""

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL, timeout=180.0)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_ctx": 3072,
                "num_predict": 1200,
                "temperature": 0.2,  # Professional, focused, deterministic
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

    # Ground with predefined standard guidance if available
    guidance_entry = GUIDANCE.get(request.check_id, {})
    why_context = request.why_th or guidance_entry.get("why_th", "ตามมาตรฐานสากล")
    remedy_context = guidance_entry.get("remediation_th", "")

    prompt = f"""คุณเป็นผู้เชี่ยวชาญอาวุโสด้าน Cybersecurity และ Web Application Security (OSCP, CISSP)
เชี่ยวชาญ OWASP Top 10, OWASP ASVS, CWE/CVE taxonomy, NIST Cybersecurity Framework
รวมถึงมาตรฐาน WCAG 2.1 (Accessibility), Core Web Vitals (Performance) และมาตรฐาน สกมช. (NCSA Thailand)

กรุณาวิเคราะห์และให้คำแนะนำวิธีแก้ไขสำหรับรายการตรวจสอบต่อไปนี้โดยอิงตามข้อเท็จจริงและมาตรฐานสากล:
- รหัสตรวจสอบ: {request.check_id}
- ชื่อรายการ: {request.check_name} ({request.check_name_th or ''})
- สถานะปัจจุบัน: {request.status}
- ปัญหาที่ตรวจพบ: {request.detail}
- ความสำคัญ/เหตุผล: {why_context}
- แนวทางมาตรฐานอ้างอิง: {remedy_context or 'ปรับปรุงตาม Best Practice'}
- ข้อมูลหลักฐานโค้ดที่พบ (Evidence):
{evidence_str or 'ไม่มีข้อมูล snippet เฉพาะจุด'}

กฎการตอบ:
1. ตอบตรงประเด็น ให้คำแนะนำที่ถูกต้องและใช้แก้ไขได้จริงตามมาตรฐาน
2. ห้ามแต่งเติมข้อมูลที่ไม่มีอยู่จริง
3. ให้ตัวอย่างโค้ดหรือการตั้งค่า (Code Snippet/Config) ที่ถูกต้องและปลอดภัย

กรุณาตอบเป็นภาษาไทยแบบกระชับ ชัดเจน และจัดรูปแบบ Markdown ดังนี้:
1. 🔍 **สาเหตุของปัญหา**: สรุปสั้นๆ 1-2 ประโยคว่าทำไมถึงไม่ผ่าน
2. 💡 **วิธีแก้ไขทีละขั้นตอน (Step-by-step)**: ข้อ 1, 2, 3 ชัดเจนและนำไปทำตามได้ทันที
3. 💻 **ตัวอย่างโค้ด/คอนฟิกที่ถูกต้อง**: ยกตัวอย่างโค้ด HTML / CSS / Nginx config หรือ JS ที่แก้ไขแล้วพร้อมคำอธิบายสั้นๆ
4. 🛡️ **คำแนะนำเสริมด้านความปลอดภัย**: ข้อควรระวังเพิ่มเติมตามมาตรฐาน
"""

    try:
        client = ollama.Client(host=OLLAMA_BASE_URL, timeout=180.0)
        response = client.generate(
            model=OLLAMA_MODEL,
            prompt=prompt,
            options={
                "num_ctx": 2048,
                "num_predict": 768,
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

        guidance_entry = GUIDANCE.get(item.check_id, {})
        why_context = guidance_entry.get("why_th", "")
        remedy_context = guidance_entry.get("remediation_th", "")

        prompt = f"""คุณเป็นผู้เชี่ยวชาญอาวุโสด้าน Cybersecurity (OSCP/CISSP) เชี่ยวชาญ OWASP Top 10, CWE/CVE, NIST CSF, MITRE ATT&CK
รวมถึง Web Accessibility (WCAG 2.1) และ Web Performance (Core Web Vitals)

วิเคราะห์ผลตรวจสอบนี้ให้กระชับ ตรงประเด็น ตอบจากข้อมูลจริงที่ตรวจพบ โดยอ้างอิงมาตรฐานสากล:
- รหัส: {item.check_id}
- รายการ: {item.check_name} ({item.check_name_th or ''})
- สถานะ: {item.status}
- ปัญหาที่พบ: {item.detail}
- ผลกระทบมาตรฐาน: {why_context or 'ส่งผลต่อความปลอดภัย/คุณภาพเว็บ'}
- แนวทางมาตรฐาน: {remedy_context or 'ปรับปรุงตาม Best Practice'}
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
                    "num_ctx": 2048,
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
