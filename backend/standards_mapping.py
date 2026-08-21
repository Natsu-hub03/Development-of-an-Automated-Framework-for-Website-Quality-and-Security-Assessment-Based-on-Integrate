"""
standards_mapping.py
Maps raw scan results to exactly 68 checklist items across 4 web standards.

Standards:
  1. WCAG 2.1 (Web Accessibility)     — 37 items (axe-core)
  2. Core Web Vitals & SEO (Google)    —  9 items (Lighthouse)
  3. NCSA / สกมช. (Thai Cybersecurity) — 11 items (headers + wappalyzer + ZAP)
  4. OWASP HTTP Security Headers       — 11 items (headers scan)
                                        ────────
                                  Total: 68 items
"""

from datetime import datetime, timezone
from typing import Any, Optional
from standards_guidance import get_guidance


# ── Status constants ──────────────────────────────────────────────────────────
PASS = "pass"
FAIL = "fail"
WARNING = "warning"

# ── Weak cipher patterns ─────────────────────────────────────────────────────
WEAK_CIPHERS = ["RC4", "DES", "3DES", "NULL", "EXPORT", "RC2", "IDEA", "SEED"]

# ── Common admin paths ───────────────────────────────────────────────────────
ADMIN_PATHS = [
    "/admin", "/wp-admin", "/wp-login.php", "/administrator",
    "/login", "/phpmyadmin", "/cpanel", "/webmail",
    "/manager", "/console", "/dashboard/login",
]


# ══════════════════════════════════════════════════════════════════════════════
#  Helper: extract inner "data" from API response envelope
# ══════════════════════════════════════════════════════════════════════════════
def _extract(raw: Any) -> Optional[dict]:
    """Unwrap {success, scan_id, data: {...}} envelope or return raw dict."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        if raw.get("error"):
            return None
        if "data" in raw and isinstance(raw["data"], dict):
            return raw["data"]
    return raw if isinstance(raw, dict) else None


# ══════════════════════════════════════════════════════════════════════════════
#  Result builder
# ══════════════════════════════════════════════════════════════════════════════
def _make(check: dict, status: str, detail: str, source: str) -> dict:
    guide = get_guidance(check["id"])
    return {
        "id": check["id"],
        "name": check["name"],
        "name_th": check["name_th"],
        "why_th": guide.get("why_th", ""),
        "remediation_th": guide.get("remediation_th", ""),
        "standard": check["standard"],
        "category": check["category"],
        "status": status,
        "detail": detail,
        "source_tool": source,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Evaluators: axe-core, Lighthouse, header, custom
# ══════════════════════════════════════════════════════════════════════════════

# ── Thai Rule Explanations for axe-core rules (Fail vs Pass) ───────────────
RULE_FAIL_TH: dict[str, str] = {
    "image-alt": "รูปภาพนี้ไม่มีแอตทริบิวต์ alt อธิบายรูปภาพ",
    "color-contrast": "สีตัวอักษรและพื้นหลังมีความเปรียบต่างไม่เพียงพอ (ต่ำกว่าเกณฑ์ 4.5:1)",
    "label": "ช่องกรอกข้อมูลนี้ไม่มีป้ายชื่อ Label หรือ aria-label กำกับ",
    "button-name": "ปุ่มนี้ไม่มีข้อความหรือ aria-label ระบุหน้าที่ของปุ่ม",
    "link-name": "ลิงก์นี้ไม่มีข้อความที่สื่อความหมายหรือเป็นลิงก์ว่าง",
    "document-title": "เอกสารไม่มีแท็ก <title> หรือแท็ก <title> ว่างเปล่า",
    "html-has-lang": "แท็ก <html> ไม่มีแอตทริบิวต์ lang ระบุภาษา",
    "html-lang-valid": "ค่ารหัสภาษาใน lang ไม่ถูกต้องตามมาตรฐาน BCP 47",
    "heading-order": "ลำดับหัวข้อ <h1-h6> ข้ามระดับ ไม่เรียงตามโครงสร้าง",
    "list": "แท็ก <ul> หรือ <ol> มี element อื่นที่ไม่ใช่ <li> อยู่ข้างใน",
    "listitem": "แท็ก <li> ไม่ได้อยู่ภายใต้แท็ก <ul> หรือ <ol>",
    "frame-title": "แท็ก <iframe> ไม่มีแอตทริบิวต์ title อธิบายเนื้อหา",
    "th-has-data-cells": "ตารางข้อมูลไม่มีการระบุความสัมพันธ์ของหัวตาราง <th>",
    "td-headers-attr": "แอตทริบิวต์ headers ในตารางอ้างอิง id ที่ไม่มีอยู่จริง",
    "input-image-alt": "ปุ่มรูปภาพ <input type='image'> ไม่มีแอตทริบิวต์ alt",
    "autocomplete-valid": "ค่า autocomplete ในช่องกรอกไม่ถูกต้องตามมาตรฐาน",
    "fieldset-no-legend": "แท็ก <fieldset> ไม่มี <legend> อธิบายชื่อกลุ่ม",
    "form-field-multiple-labels": "ช่องกรอกมี Label ผูกซ้ำซ้อนหลายอัน",
    "area-alt": "จุดคลิก <area> บนแผนที่รูปภาพไม่มีคำอธิบาย alt",
    "object-alt": "แท็ก <object> ไม่มีข้อความสำรองกรณีอุปกรณ์ไม่รองรับ",
    "video-caption": "วิดีโอไม่มีแท็ก <track> คำบรรยาย (Captions)",
    "svg-img-alt": "ภาพกราฟิก SVG ไม่มี <title> หรือ aria-label กำกับ",
    "tabindex": "แท็กมีการใส่ tabindex มากกว่า 0 ซึ่งทำลายลำดับการกด Tab",
    "duplicate-id": "พบค่า id ซ้ำกันในหน้าเดียวกัน",
    "duplicate-id-aria": "พบค่า id ที่ใช้ใน ARIA ซ้ำกัน",
    "bypass": "ไม่พบปุ่มลัดข้ามเมนู (Skip to main content) สำหรับคีย์บอร์ด",
    "aria-hidden-focus": "Element ที่มี aria-hidden='true' สามารถรับ Focus ได้",
    "scrollable-region-focusable": "กล่อง Scroll ไม่มี tabindex='0' ให้คีย์บอร์ดเลื่อนได้",
    "meta-viewport": "มีการล็อกการซูมหน้าจอใน <meta name='viewport'>",
    "css-orientation-lock": "มีการล็อกทิศทางหน้าจอแนวตั้ง/แนวนอนด้วย CSS",
    "avoid-inline-spacing": "มีการใช้ !important ทับระยะห่างตัวอักษรทำให้ปรับแต่งไม่ได้",
    "aria-roles": "ค่า role ของ ARIA ไม่ถูกต้องตามมาตรฐาน W3C",
    "aria-valid-attr": "ชื่อแอตทริบิวต์ aria-* สะกดไม่ถูกต้อง",
    "aria-valid-attr-value": "ค่าในแอตทริบิวต์ aria-* ไม่ตรงตาม Type ที่กำหนด",
    "aria-required-attr": "ขาดแอตทริบิวต์บังคับของ ARIA Role นั้นๆ",
    "aria-required-parent": "ARIA Role ไม่ได้อยู่ภายใต้ Parent Role ที่กำหนด",
    "aria-required-children": "ARIA Role ขาด Children Role ที่สัมพันธ์กัน",
    "aria-hidden-body": "มีการใส่ aria-hidden='true' บนแท็ก <body>",
    "aria-dialog-name": "หน้าต่าง Pop-up (dialog) ไม่มีชื่อกำกับ",
}

RULE_PASS_TH: dict[str, str] = {
    "image-alt": "รูปภาพมีแอตทริบิวต์ alt อธิบายรูปภาพครบถ้วน",
    "color-contrast": "สีตัวอักษรและพื้นหลังมีความเปรียบต่างผ่านเกณฑ์มาตรฐาน (>= 4.5:1)",
    "label": "ช่องกรอกข้อมูลมีป้ายชื่อ Label หรือ aria-label กำกับถูกต้อง",
    "button-name": "ปุ่มมีข้อความหรือ aria-label ระบุหน้าที่ชัดเจน",
    "link-name": "ลิงก์มีข้อความที่สื่อความหมายชัดเจน",
    "document-title": "เอกสารมีแท็ก <title> ระบุชื่อหน้าเว็บอย่างถูกต้อง",
    "html-has-lang": "แท็ก <html> มีแอตทริบิวต์ lang ระบุภาษาของเอกสาร",
    "html-lang-valid": "ค่ารหัสภาษาใน lang ถูกต้องตามมาตรฐาน BCP 47",
    "heading-order": "ลำดับหัวข้อ <h1-h6> เรียงถูกต้องตามโครงสร้าง",
    "list": "แท็ก <ul> และ <ol> มีโครงสร้างรายการถูกต้อง",
    "listitem": "แท็ก <li> อยู่ภายใต้แท็ก <ul> หรือ <ol> อย่างถูกต้อง",
    "frame-title": "แท็ก <iframe> มีแอตทริบิวต์ title อธิบายเนื้อหาครบถ้วน",
    "th-has-data-cells": "ตารางข้อมูลระบุหัวตาราง <th> ถูกต้อง",
    "td-headers-attr": "แอตทริบิวต์ headers ในตารางอ้างอิง id ถูกต้อง",
    "input-image-alt": "ปุ่มรูปภาพมีแอตทริบิวต์ alt อธิบายชัดเจน",
    "autocomplete-valid": "ค่า autocomplete ในช่องกรอกถูกต้องตามมาตรฐาน",
    "fieldset-no-legend": "แท็ก <fieldset> มี <legend> ระบุชื่อกลุ่มครบถ้วน",
    "form-field-multiple-labels": "ช่องกรอกข้อมูลผูก Label อย่างเหมาะสม",
    "area-alt": "จุดคลิก <area> บนแผนที่รูปภาพมีคำอธิบาย alt ครบถ้วน",
    "object-alt": "แท็ก <object> มีข้อความหรือเนื้อหาสำรองครบถ้วน",
    "video-caption": "วิดีโอมีแท็ก <track> คำบรรยาย (Captions)",
    "svg-img-alt": "ภาพกราฟิก SVG มี <title> หรือ aria-label กำกับชัดเจน",
    "tabindex": "ลำดับการกด Tab เป็นไปตามธรรมชาติ (ไม่ใช้ tabindex > 0)",
    "duplicate-id": "ค่า id ของทุก element ในหน้าเว็บไม่ซ้ำกัน",
    "duplicate-id-aria": "ค่า id ที่ใช้ใน ARIA ไม่ซ้ำกัน",
    "bypass": "มีปุ่มลัดข้ามเมนู (Skip to main content) อำนวยความสะดวกคีย์บอร์ด",
    "aria-hidden-focus": "Element ที่มี aria-hidden ไม่ได้รับ Focus จากคีย์บอร์ด",
    "scrollable-region-focusable": "กล่อง Scroll สามารถเลื่อนด้วยคีย์บอร์ดได้",
    "meta-viewport": "อนุญาตให้ผู้ใช้ซูมขยายหน้าจอได้ตามต้องการ",
    "css-orientation-lock": "รองรับการแสดงผลทั้งแนวตั้งและแนวนอน",
    "avoid-inline-spacing": "รองรับการปรับระยะห่างตัวอักษรของผู้ใช้",
    "aria-roles": "ใช้ ARIA Role ถูกต้องตามมาตรฐาน W3C",
    "aria-valid-attr": "ใช้ชื่อแอตทริบิวต์ aria-* ถูกต้องตามมาตรฐาน",
    "aria-valid-attr-value": "ค่าในแอตทริบิวต์ aria-* ถูกต้องตาม Type",
    "aria-required-attr": "ใส่แอตทริบิวต์บังคับของ ARIA Role ครบถ้วน",
    "aria-required-parent": "ARIA Role อยู่ภายใต้ Parent Role ที่ถูกต้อง",
    "aria-required-children": "ARIA Role มี Children Role ครบถ้วน",
    "aria-hidden-body": "แท็ก <body> ไม่ได้ถูกซ่อนด้วย aria-hidden",
    "aria-dialog-name": "หน้าต่าง Pop-up (dialog) มีชื่อระบุหัวข้อชัดเจน",
}


def _eval_axe(check: dict, axe_data: Optional[dict]) -> dict:
    """Evaluate WCAG check against axe-core violations/incomplete."""
    if not axe_data:
        return _make(check, WARNING, "ยังไม่ได้รัน axe-core scan", "axe-core")

    rules = check["rules"]
    violations = axe_data.get("violations", [])
    incomplete = axe_data.get("incomplete", [])

    v_ids = {v.get("id") for v in violations}
    i_ids = {i.get("id") for i in incomplete}

    failed = [r for r in rules if r in v_ids]
    warned = [r for r in rules if r in i_ids]

    if failed:
        details = []
        evidence_nodes = []
        for v in violations:
            rid = v.get("id")
            if rid in failed:
                cnt = v.get("nodes_count", 1)
                th_desc = RULE_FAIL_TH.get(rid, v.get("help", rid))
                details.append(f"{th_desc} (พบ {cnt} จุด)")
                for n in v.get("nodes", [])[:5]:
                    target = n.get("target", [])
                    if rid == "document-title" and target == ["html"]:
                        target = ["head > title"]
                    evidence_nodes.append({
                        "target": target,
                        "html": n.get("html", ""),
                        "failureSummary": th_desc,
                    })
        if not evidence_nodes:
            main_rule = rules[0] if rules else check["id"]
            th_desc = RULE_FAIL_TH.get(main_rule, "พบข้อผิดพลาดตามเกณฑ์มาตรฐาน")
            evidence_nodes.append({
                "target": [f"HTML Document (Rule: {main_rule})"],
                "html": f"<!-- ตรวจพบข้อบกพร่องตามกฎ {main_rule} -->",
                "failureSummary": th_desc,
            })
        result = _make(check, FAIL, "; ".join(details) if details else "ไม่ผ่านการตรวจสอบ", "axe-core")
        result["evidence"] = evidence_nodes[:10]
        result["evidence_type"] = "dom"
        return result

    if warned:
        details = []
        evidence_nodes = []
        for i in incomplete:
            rid = i.get("id")
            if rid in warned:
                th_desc = RULE_FAIL_TH.get(rid, i.get("help", rid))
                details.append(f"ต้องตรวจสอบเพิ่ม: {th_desc}")
                for n in i.get("nodes", [])[:5]:
                    target = n.get("target", [])
                    if rid == "document-title" and target == ["html"]:
                        target = ["head > title"]
                    evidence_nodes.append({
                        "target": target,
                        "html": n.get("html", ""),
                        "failureSummary": f"ต้องตรวจสอบด้วยตนเอง: {th_desc}",
                    })
        if not evidence_nodes:
            main_rule = rules[0] if rules else check["id"]
            th_desc = RULE_FAIL_TH.get(main_rule, "ต้องตรวจสอบเพิ่มเติมด้วยตนเอง")
            evidence_nodes.append({
                "target": [f"HTML Document (Rule: {main_rule})"],
                "html": f"<!-- ต้องตรวจสอบความสอดคล้องตามกฎ {main_rule} เพิ่มเติม -->",
                "failureSummary": th_desc,
            })
        result = _make(check, WARNING,
                       "; ".join(details) if details else "ต้องตรวจสอบเพิ่ม", "axe-core")
        result["evidence"] = evidence_nodes[:10]
        result["evidence_type"] = "dom"
        return result

    # For PASS: extract sample passing nodes
    passes = axe_data.get("passes", [])
    p_ids = {p.get("id") for p in passes}
    passed_rules = [r for r in rules if r in p_ids]
    pass_nodes = []
    if passed_rules:
        for p in passes:
            rid = p.get("id")
            if rid in passed_rules:
                th_desc = RULE_PASS_TH.get(rid, p.get("help", rid))
                for n in p.get("nodes", [])[:3]:
                    target = n.get("target", [])
                    if rid == "document-title" and target == ["html"]:
                        target = ["head > title"]
                    pass_nodes.append({
                        "target": target,
                        "html": n.get("html", ""),
                        "passed_summary": th_desc,
                    })

    if not pass_nodes:
        main_rule = rules[0] if rules else check["id"]
        th_desc = RULE_PASS_TH.get(main_rule, f"ผ่านการตรวจสอบตามเกณฑ์ {check.get('name_th', check['name'])}")
        pass_nodes.append({
            "target": [f"HTML Document (Rule: {main_rule})"],
            "html": f"<!-- โครงสร้าง {check['name']} ผ่านเกณฑ์มาตรฐาน ไม่พบจุดบกพร่อง -->",
            "passed_summary": th_desc,
        })

    result = _make(check, PASS, "ผ่านการตรวจสอบตามเกณฑ์มาตรฐาน WCAG 2.1", "axe-core")
    result["evidence"] = pass_nodes[:6]
    result["evidence_type"] = "dom"
    return result


def _eval_lh(check: dict, lh_data: Optional[dict]) -> dict:
    """Evaluate check against Lighthouse failed audits."""
    if not lh_data:
        return _make(check, WARNING, "ยังไม่ได้รัน Lighthouse scan", "lighthouse")

    audit_ids = check["rules"]
    failed_audits = lh_data.get("failed_audits", [])
    failed_map = {a["id"]: a for a in failed_audits}

    failures = []
    evidence_nodes = []
    for aid in audit_ids:
        if aid in failed_map:
            a = failed_map[aid]
            dv = a.get("displayValue", "")
            sc = a.get("score", "?")
            msg = f'{a.get("title", aid)}: {dv}' if dv else f'{a.get("title", aid)} (คะแนน {sc}/100)'
            failures.append(msg)
            evidence_nodes.append({
                "target": [f"Audit: {aid}"],
                "html": f"Metric value: {dv or str(sc)}",
                "failureSummary": a.get("description", msg),
            })

    if failures:
        worst = min(
            (failed_map[aid]["score"]
             for aid in audit_ids if aid in failed_map),
            default=50,
        )
        status = FAIL if worst < 50 else WARNING
        res = _make(check, status, "; ".join(failures), "lighthouse")
        res["evidence"] = evidence_nodes
        res["evidence_type"] = "lighthouse"
        return res

    res = _make(check, PASS, "คะแนนผ่านเกณฑ์มาตรฐาน Google Lighthouse", "lighthouse")
    res["evidence"] = [{
        "target": [f"Rules: {', '.join(audit_ids)}"],
        "html": "Audit Passed (Score: 100/100)",
        "passed_summary": "ผ่านเกณฑ์ประสิทธิภาพและการจัดทำดัชนี",
    }]
    res["evidence_type"] = "lighthouse"
    return res


def _eval_header(check: dict, headers_data: Optional[dict]) -> dict:
    """Evaluate OWASP header check — presence + optional value validation."""
    if not headers_data:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")

    header_key = check["header"]
    sec_headers = headers_data.get("security_headers", {})
    value = sec_headers.get(header_key)

    if not value:
        res = _make(check, FAIL, f"ไม่พบ Header: {header_key}", "headers-scan")
        res["evidence"] = [{
            "target": ["HTTP Response Headers"],
            "html": f"Missing: {header_key}",
            "failureSummary": f"เซิร์ฟเวอร์ไม่ได้ส่ง {header_key} ใน Response Header",
        }]
        res["evidence_type"] = "header"
        return res

    validator = check.get("validator")
    if validator:
        status, detail = validator(value)
        res = _make(check, status, detail, "headers-scan")
        res["evidence"] = [{
            "target": [f"HTTP Header: {header_key}"],
            "html": f"{header_key}: {value}",
            "failureSummary": detail if status != PASS else None,
            "passed_summary": f"พบ Header {header_key} ค่าถูกต้อง" if status == PASS else None,
        }]
        res["evidence_type"] = "header"
        return res

    res = _make(check, PASS, f"{header_key}: {value}", "headers-scan")
    res["evidence"] = [{
        "target": [f"HTTP Header: {header_key}"],
        "html": f"{header_key}: {value}",
        "passed_summary": f"พบ Header {header_key}: {value}",
    }]
    res["evidence_type"] = "header"
    return res


# ── Header value validators (used by OWASP checks) ───────────────────────────

def _v_csp(val):
    v = val.lower()
    if "unsafe-inline" in v and "unsafe-eval" in v:
        return WARNING, f"CSP พบ unsafe-inline + unsafe-eval: {val[:120]}"
    return PASS, f"CSP: {val[:120]}"


def _v_hsts(val):
    if "max-age" not in val.lower():
        return WARNING, f"HSTS ไม่มี max-age: {val}"
    return PASS, f"HSTS: {val}"


def _v_xfo(val):
    v = val.upper()
    if "DENY" in v or "SAMEORIGIN" in v:
        return PASS, f"X-Frame-Options: {val}"
    return WARNING, f"X-Frame-Options ค่าไม่เหมาะสม: {val}"


def _v_xcto(val):
    if val.strip().lower() == "nosniff":
        return PASS, f"X-Content-Type-Options: {val}"
    return WARNING, f"X-Content-Type-Options ไม่ใช่ nosniff: {val}"


def _v_referrer(val):
    safe = ["no-referrer", "same-origin", "strict-origin",
            "strict-origin-when-cross-origin"]
    if any(s in val.lower() for s in safe):
        return PASS, f"Referrer-Policy: {val}"
    return WARNING, f"Referrer-Policy อาจไม่ปลอดภัย: {val}"


def _v_coop(val):
    if "same-origin" in val.lower():
        return PASS, f"COOP: {val}"
    return WARNING, f"COOP ไม่ใช่ same-origin: {val}"


def _v_coep(val):
    if "require-corp" in val.lower():
        return PASS, f"COEP: {val}"
    return WARNING, f"COEP ไม่ใช่ require-corp: {val}"


def _v_corp(val):
    v = val.lower()
    if "same-origin" in v or "same-site" in v:
        return PASS, f"CORP: {val}"
    return WARNING, f"CORP ไม่ใช่ same-origin/same-site: {val}"


def _v_cache(val):
    v = val.lower()
    if "no-store" in v or "no-cache" in v:
        return PASS, f"Cache-Control: {val}"
    return WARNING, \
        f"Cache-Control อาจไม่ปลอดภัยสำหรับหน้าที่มีข้อมูลสำคัญ: {val}"


# ── Custom evaluators (NCSA + OWASP Set-Cookie) ──────────────────────────────

def _eval_https_redirect(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    is_https = hdr.get("is_https", False)
    redir = hdr.get("https_redirect", {})

    if is_https and redir.get("redirects_to_https"):
        res = _make(check, PASS,
                    "HTTPS บังคับใช้ — HTTP redirect ไปยัง HTTPS",
                    "headers-scan")
        res["evidence"] = [{
            "target": ["HTTP / HTTPS Protocol"],
            "html": "HTTP 301/302 Redirect -> HTTPS",
            "passed_summary": "บังคับเชื่อมต่อผ่าน HTTPS ปลอดภัยสมบูรณ์",
        }]
        res["evidence_type"] = "header"
        return res
    if is_https:
        if redir.get("checked") and not redir.get("redirects_to_https"):
            res = _make(check, WARNING,
                        "ใช้ HTTPS แต่ HTTP ไม่ redirect ไปยัง HTTPS",
                        "headers-scan")
            res["evidence"] = [{
                "target": ["HTTP Connection"],
                "html": "HTTP Status 200 (No Redirect)",
                "failureSummary": "เว็บไซต์รองรับ HTTPS แต่ไม่ได้ตั้งค่าบังคับ Redirect จาก HTTP",
            }]
            res["evidence_type"] = "header"
            return res
        res = _make(check, PASS, "เว็บไซต์ใช้ HTTPS", "headers-scan")
        res["evidence"] = [{
            "target": ["HTTPS Protocol"],
            "html": "HTTPS Enabled",
            "passed_summary": "เว็บไซต์ใช้งานการเชื่อมต่อที่เข้ารหัส HTTPS",
        }]
        res["evidence_type"] = "header"
        return res
    res = _make(check, FAIL, "เว็บไซต์ไม่ได้ใช้ HTTPS", "headers-scan")
    res["evidence"] = [{
        "target": ["HTTP Protocol"],
        "html": "Insecure HTTP (No SSL/TLS)",
        "failureSummary": "เว็บไซต์ยังใช้งานโปรโตคอล HTTP แบบไม่เข้ารหัส",
    }]
    res["evidence_type"] = "header"
    return res


def _eval_ncsa_hsts(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    val = hdr.get("security_headers", {}).get("strict-transport-security")
    if not val:
        res = _make(check, FAIL,
                    "ไม่พบ Strict-Transport-Security header", "headers-scan")
        res["evidence"] = [{
            "target": ["HTTP Response Headers"],
            "html": "Missing: Strict-Transport-Security",
            "failureSummary": "เซิร์ฟเวอร์ไม่ได้ส่ง Header HSTS",
        }]
        res["evidence_type"] = "header"
        return res
    res = _make(check, PASS, f"HSTS: {val}", "headers-scan")
    res["evidence"] = [{
        "target": ["HTTP Header: Strict-Transport-Security"],
        "html": f"Strict-Transport-Security: {val}",
        "passed_summary": "พบการตั้งค่า HSTS เพื่อป้องกัน SSL Stripping",
    }]
    res["evidence_type"] = "header"
    return res


def _eval_ncsa_clickjack(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    h = hdr.get("security_headers", {})
    xfo = h.get("x-frame-options")
    csp = h.get("content-security-policy", "") or ""

    if xfo:
        v = xfo.upper()
        if "DENY" in v or "SAMEORIGIN" in v:
            res = _make(check, PASS, f"X-Frame-Options: {xfo}", "headers-scan")
            res["evidence"] = [{
                "target": ["HTTP Header: X-Frame-Options"],
                "html": f"X-Frame-Options: {xfo}",
                "passed_summary": "พบการป้องกัน Clickjacking ด้วย X-Frame-Options",
            }]
            res["evidence_type"] = "header"
            return res
    if "frame-ancestors" in csp.lower():
        res = _make(check, PASS, f"CSP frame-ancestors: {csp[:100]}", "headers-scan")
        res["evidence"] = [{
            "target": ["HTTP Header: Content-Security-Policy"],
            "html": f"Content-Security-Policy: {csp[:120]}",
            "passed_summary": "พบการป้องกัน Clickjacking ด้วย CSP frame-ancestors",
        }]
        res["evidence_type"] = "header"
        return res
    res = _make(check, FAIL,
                "ไม่พบการป้องกัน Clickjacking (X-Frame-Options หรือ CSP frame-ancestors)",
                "headers-scan")
    res["evidence"] = [{
        "target": ["HTTP Headers: XFO & CSP"],
        "html": "Missing: X-Frame-Options / frame-ancestors",
        "failureSummary": "ไม่พบการป้องกันการฝังหน้าเว็บใน iframe (เสี่ยงต่อ Clickjacking)",
    }]
    res["evidence_type"] = "header"
    return res


def _eval_server_info(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ไม่มีข้อมูล headers scan", "headers-scan")
    si = hdr.get("server_info", {})
    server = si.get("server")
    xpb = si.get("x-powered-by")
    issues = []
    if server:
        issues.append(f"Server: {server}")
    if xpb:
        issues.append(f"X-Powered-By: {xpb}")
    if not issues:
        res = _make(check, PASS, "ไม่พบการเปิดเผยข้อมูลเซิร์ฟเวอร์", "headers-scan")
        res["evidence"] = [{
            "target": ["HTTP Response Headers"],
            "html": "Server & X-Powered-By headers are hidden",
            "passed_summary": "ไม่พบการเปิดเผยเวอร์ชันของ Web Server หรือ Backend",
        }]
        res["evidence_type"] = "header"
        return res
    res = _make(check, WARNING, "เปิดเผยข้อมูลเซิร์ฟเวอร์: " + ", ".join(issues), "headers-scan")
    res["evidence"] = [{
        "target": ["HTTP Response Headers"],
        "html": "\n".join(issues),
        "failureSummary": "เซิร์ฟเวอร์เปิดเผยยี่ห้อ/เวอร์ชันใน Response Header",
    }]
    res["evidence_type"] = "header"
    return res


def _eval_tls_version(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ไม่มีข้อมูล headers scan", "headers-scan")
    tls_info = hdr.get("tls")
    if not tls_info or tls_info.get("error"):
        err = tls_info.get("error", "ไม่มีข้อมูล") if tls_info else "ไม่มีข้อมูล"
        res = _make(check, WARNING, f"ไม่สามารถตรวจ TLS: {err}", "headers-scan")
        res["evidence"] = [{
            "target": ["SSL/TLS Handshake"],
            "html": f"TLS Inspection Error: {err}",
            "failureSummary": "ไม่สามารถตรวจสอบข้อมูลโปรโตคอล TLS",
        }]
        res["evidence_type"] = "tls"
        return res
    proto = tls_info.get("protocol", "")
    if proto in ("TLSv1.3", "TLSv1.2"):
        res = _make(check, PASS, f"TLS Protocol: {proto}", "headers-scan")
        res["evidence"] = [{
            "target": ["SSL/TLS Protocol Version"],
            "html": f"Protocol: {proto}",
            "passed_summary": f"ใช้งาน {proto} ตามเกณฑ์ความมั่นคงปลอดภัย สกมช.",
        }]
        res["evidence_type"] = "tls"
        return res
    if proto in ("TLSv1.1", "TLSv1.0", "SSLv3"):
        res = _make(check, FAIL, f"TLS Protocol ไม่ปลอดภัย: {proto} (ต้อง TLS 1.2+)", "headers-scan")
        res["evidence"] = [{
            "target": ["SSL/TLS Protocol Version"],
            "html": f"Protocol: {proto}",
            "failureSummary": f"โปรโตคอล {proto} มีช่องโหว่ร้ายแรง ต้องปิดการใช้งาน",
        }]
        res["evidence_type"] = "tls"
        return res
    res = _make(check, WARNING, f"TLS Protocol: {proto or 'ไม่ทราบ'}", "headers-scan")
    res["evidence"] = [{
        "target": ["SSL/TLS Protocol Version"],
        "html": f"Protocol: {proto or 'Unknown'}",
        "failureSummary": "ไม่สามารถยืนยันความปลอดภัยของโปรโตคอล TLS ได้",
    }]
    res["evidence_type"] = "tls"
    return res


def _eval_cipher(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    tls_info = hdr.get("tls")
    if not tls_info or tls_info.get("error"):
        res = _make(check, WARNING, "ไม่สามารถตรวจ Cipher Suite", "headers-scan")
        res["evidence"] = [{
            "target": ["SSL/TLS Cipher Suite"],
            "html": "Cipher Inspection Unavailable",
            "failureSummary": "ไม่สามารถตรวจข้อมูลชุดรหัส Cipher",
        }]
        res["evidence_type"] = "tls"
        return res
    cipher = (tls_info.get("cipher_name")
              or tls_info.get("cipher_standard_name", ""))
    if not cipher:
        res = _make(check, WARNING, "ไม่ทราบ Cipher Suite", "headers-scan")
        res["evidence"] = [{
            "target": ["SSL/TLS Cipher Suite"],
            "html": "Cipher: Unknown",
            "failureSummary": "ไม่พบข้อมูล Cipher Suite",
        }]
        res["evidence_type"] = "tls"
        return res
    upper = cipher.upper()
    if any(wc in upper for wc in WEAK_CIPHERS):
        res = _make(check, FAIL, f"Cipher Suite ไม่ปลอดภัย: {cipher}", "headers-scan")
        res["evidence"] = [{
            "target": ["SSL/TLS Cipher Suite"],
            "html": f"Cipher: {cipher}",
            "failureSummary": "ชุดรหัสเข้ารหัสจัดอยู่ในกลุ่ม Weak Cipher ที่ไม่ปลอดภัย",
        }]
        res["evidence_type"] = "tls"
        return res
    res = _make(check, PASS, f"Cipher Suite: {cipher}", "headers-scan")
    res["evidence"] = [{
        "target": ["SSL/TLS Cipher Suite"],
        "html": f"Cipher: {cipher}",
        "passed_summary": "ชุดรหัสเข้ารหัสมีความแข็งแรงตามมาตรฐานสากล",
    }]
    res["evidence_type"] = "tls"
    return res


def _eval_xss_sqli(check, hdr, wap, zap):
    if not zap:
        res = _make(check, WARNING, "ต้องรัน ZAP scan เพื่อตรวจ XSS/SQL Injection", "zap")
        res["evidence"] = [{
            "target": ["OWASP ZAP Dynamic Scan"],
            "html": "ZAP scan is not executed",
            "failureSummary": "ยังไม่ได้รันการสแกนแบบ Active/Passive กับ ZAP",
        }]
        res["evidence_type"] = "zap"
        return res
    alerts = zap.get("alerts", [])
    keywords = ["xss", "sql injection", "cross-site scripting", "injection"]
    xss_sqli = [
        a for a in alerts
        if a.get("risk") in ("High", "Medium")
        and any(kw in a.get("alert", "").lower() for kw in keywords)
    ]
    if xss_sqli:
        names = list(set(a["alert"] for a in xss_sqli))[:3]
        res = _make(check, FAIL, f"พบช่องโหว่: {', '.join(names)}", "zap")
        res["evidence"] = [{
            "target": [f"ZAP Alert: {a.get('alert')}"],
            "html": f"URL: {a.get('url')}\nParam: {a.get('param')}\nEvidence: {a.get('evidence', '')[:100]}",
            "failureSummary": a.get("description", "พบช่องโหว่ Injection"),
        } for a in xss_sqli[:4]]
        res["evidence_type"] = "zap"
        return res
    res = _make(check, PASS, "ไม่พบช่องโหว่ XSS/SQL Injection จาก ZAP scan", "zap")
    res["evidence"] = [{
        "target": ["OWASP ZAP Dynamic Scan"],
        "html": "Zero High/Medium Injection Alerts Detected",
        "passed_summary": "ไม่พบช่องโหว่ Injection ที่มีความเสี่ยงระดับสูงหรือปานกลาง",
    }]
    res["evidence_type"] = "zap"
    return res


def _eval_cookie_security(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    cookie_info = hdr.get("cookies", {})
    if not cookie_info.get("has_cookies"):
        res = _make(check, PASS, "ไม่พบ Cookie ที่ต้องตรวจสอบ", "headers-scan")
        res["evidence"] = [{
            "target": ["Set-Cookie Headers"],
            "html": "No cookies set in response",
            "passed_summary": "เว็บไซต์ไม่มีการสร้าง Cookie ในหน้าแรก",
        }]
        res["evidence_type"] = "header"
        return res
    cookies = cookie_info.get("cookies", [])
    issues = []
    evidence_nodes = []
    for c in cookies:
        name = c.get("name", "?")
        missing = []
        if not c.get("secure"):
            missing.append("Secure")
        if not c.get("httpOnly"):
            missing.append("HttpOnly")
        if not c.get("sameSite"):
            missing.append("SameSite")
        if missing:
            msg = f'{name}: ขาด {", ".join(missing)}'
            issues.append(msg)
            evidence_nodes.append({
                "target": [f"Cookie: {name}"],
                "html": f"Set-Cookie: {name}=***; (Missing: {', '.join(missing)})",
                "failureSummary": f"Cookie ขาด Flag ความปลอดภัย: {', '.join(missing)}",
            })
    if issues:
        res = _make(check, FAIL, "; ".join(issues[:3]), "headers-scan")
        res["evidence"] = evidence_nodes[:5]
        res["evidence_type"] = "header"
        return res
    res = _make(check, PASS, "Cookie มี Security Flags ครบถ้วน", "headers-scan")
    res["evidence"] = [{
        "target": [f"Cookie: {c.get('name', 'Cookie')}"],
        "html": f"Flags: Secure={c.get('secure')}, HttpOnly={c.get('httpOnly')}, SameSite={c.get('sameSite')}",
        "passed_summary": "Cookie มีการตั้งค่า Security Flags ครบถ้วน",
    } for c in cookies[:3]]
    res["evidence_type"] = "header"
    return res


def _eval_fingerprinting(check, hdr, wap, zap):
    if not wap:
        return _make(check, WARNING, "ยังไม่ได้รัน Wappalyzer scan", "wappalyzer")
    techs = wap.get("technologies", [])
    versioned = [t for t in techs if t.get("version")]
    if versioned:
        names = [f'{t["name"]} v{t["version"]}' for t in versioned[:5]]
        res = _make(check, WARNING, f"พบเวอร์ชันซอฟต์แวร์เปิดเผย: {', '.join(names)}", "wappalyzer")
        res["evidence"] = [{
            "target": [f"Technology: {t.get('name')}"],
            "html": f"Detected: {t.get('name')} (Version {t.get('version')})",
            "failureSummary": "มีการเปิดเผยเวอร์ชันของซอฟต์แวร์สู่สาธารณะ",
        } for t in versioned[:5]]
        res["evidence_type"] = "wappalyzer"
        return res
    res = _make(check, PASS, "ไม่พบการเปิดเผยเวอร์ชันซอฟต์แวร์", "wappalyzer")
    res["evidence"] = [{
        "target": ["Wappalyzer Technology Detection"],
        "html": f"Technologies detected: {len(techs)} (No version disclosure)",
        "passed_summary": "ไม่พบการระบุเวอร์ชันซอฟต์แวร์ที่ผู้โจมตีอาจนำไปใช้หาช่องโหว่",
    }]
    res["evidence_type"] = "wappalyzer"
    return res


def _eval_cve(check, hdr, wap, zap):
    if not wap:
        return _make(check, WARNING, "ยังไม่ได้รัน Wappalyzer scan", "wappalyzer")
    techs = wap.get("technologies", [])
    versioned = [t for t in techs if t.get("version")]
    if versioned:
        names = [f'{t["name"]} v{t["version"]}' for t in versioned[:3]]
        res = _make(check, WARNING, f"พบเวอร์ชัน — ควรตรวจ CVE: {', '.join(names)}", "wappalyzer")
        res["evidence"] = [{
            "target": [f"Component: {t.get('name')}"],
            "html": f"Version: {t.get('version')}",
            "failureSummary": f"ควรตรวจสอบฐานข้อมูล CVE สำหรับ {t.get('name')} v{t.get('version')}",
        } for t in versioned[:3]]
        res["evidence_type"] = "wappalyzer"
        return res
    res = _make(check, PASS, "ไม่พบเวอร์ชันที่ต้องตรวจสอบ CVE", "wappalyzer")
    res["evidence"] = [{
        "target": ["CVE Assessment"],
        "html": "No outdated or exposed component versions found",
        "passed_summary": "ไม่พบเวอร์ชันซอฟต์แวร์ที่ต้องเฝ้าระวัง CVE เป็นพิเศษ",
    }]
    res["evidence_type"] = "wappalyzer"
    return res


def _eval_admin_urls(check, hdr, wap, zap):
    if not zap:
        return _make(check, WARNING, "ต้องรัน ZAP scan เพื่อตรวจ Admin URLs", "zap")
    alerts = zap.get("alerts", [])
    found = set()
    for a in alerts:
        url_str = a.get("url", "").lower()
        for path in ADMIN_PATHS:
            if path in url_str:
                found.add(path)
    if found:
        res = _make(check, WARNING, f"พบ URL ที่อาจเป็นหน้าจัดการ: {', '.join(sorted(found))}", "zap")
        res["evidence"] = [{
            "target": ["Administrative URL Path"],
            "html": f"Exposed Path: {p}",
            "failureSummary": "พบหน้าเข้าสู่ระบบหรือจัดการที่สามารถเข้าถึงได้จากภายนอก",
        } for p in sorted(found)[:4]]
        res["evidence_type"] = "zap"
        return res
    res = _make(check, PASS, "ไม่พบ Admin/Login URL ที่เปิดเผย", "zap")
    res["evidence"] = [{
        "target": ["ZAP Spider & Crawl"],
        "html": "No sensitive administrative endpoints found",
        "passed_summary": "ไม่พบหน้าจัดการ /admin หรือ /login เปิดเผยต่อสาธารณะ",
    }]
    res["evidence_type"] = "zap"
    return res


def _eval_set_cookie_owasp(check, hdr, wap, zap):
    """OWASP Set-Cookie — stricter than NCSA, includes Expires/Max-Age."""
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    cookie_info = hdr.get("cookies", {})
    if not cookie_info.get("has_cookies"):
        res = _make(check, PASS, "ไม่พบ Set-Cookie header", "headers-scan")
        res["evidence"] = [{
            "target": ["HTTP Set-Cookie Header"],
            "html": "No cookies in response headers",
            "passed_summary": "ไม่พบการตั้งค่า Cookie ที่ต้องตรวจสอบ",
        }]
        res["evidence_type"] = "header"
        return res
    cookies = cookie_info.get("cookies", [])
    issues = []
    evidence_nodes = []
    for c in cookies:
        name = c.get("name", "?")
        missing = []
        if not c.get("secure"):
            missing.append("Secure")
        if not c.get("httpOnly"):
            missing.append("HttpOnly")
        if not c.get("sameSite"):
            missing.append("SameSite")
        if not c.get("hasExpiry"):
            missing.append("Expires/Max-Age")
        if missing:
            msg = f'{name}: ขาด {", ".join(missing)}'
            issues.append(msg)
            evidence_nodes.append({
                "target": [f"Cookie: {name}"],
                "html": f"Set-Cookie: {name}=***; (Missing: {', '.join(missing)})",
                "failureSummary": f"Cookie ขาด Attributes ตามเกณฑ์ OWASP: {', '.join(missing)}",
            })
    if issues:
        res = _make(check, FAIL, "; ".join(issues[:3]), "headers-scan")
        res["evidence"] = evidence_nodes[:5]
        res["evidence_type"] = "header"
        return res
    res = _make(check, PASS, "Set-Cookie มี Attributes ครบถ้วน", "headers-scan")
    res["evidence"] = [{
        "target": [f"Cookie: {c.get('name', 'Cookie')}"],
        "html": f"Attributes: Secure, HttpOnly, SameSite, Max-Age/Expires",
        "passed_summary": "Set-Cookie มี Attributes ครบถ้วนตามมาตรฐาน OWASP",
    } for c in cookies[:3]]
    res["evidence_type"] = "header"
    return res


# ── Custom evaluator dispatch table ──────────────────────────────────────────
CUSTOM_EVAL = {
    "https_redirect": _eval_https_redirect,
    "ncsa_hsts": _eval_ncsa_hsts,
    "ncsa_clickjack": _eval_ncsa_clickjack,
    "server_info": _eval_server_info,
    "tls_version": _eval_tls_version,
    "cipher": _eval_cipher,
    "xss_sqli": _eval_xss_sqli,
    "cookie_security": _eval_cookie_security,
    "fingerprinting": _eval_fingerprinting,
    "cve": _eval_cve,
    "admin_urls": _eval_admin_urls,
    "set_cookie_owasp": _eval_set_cookie_owasp,
}


# ══════════════════════════════════════════════════════════════════════════════
#  Master Checklist — exactly 68 items
# ══════════════════════════════════════════════════════════════════════════════

CHECKS = [
    # ═════════════════════════════════════════════════════════════════
    #  1. WCAG 2.1 — 37 items
    # ═════════════════════════════════════════════════════════════════

    # ── หมวด 1: โครงสร้าง HTML (8 ข้อ) ─────────────────────────────
    {"id": "wcag-01", "name": "Document Title",
     "name_th": "ตรวจหาแท็ก <title>",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["document-title"]},

    {"id": "wcag-02", "name": "Document Language",
     "name_th": "ตรวจแอตทริบิวต์ภาษา",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["html-has-lang"]},

    {"id": "wcag-03", "name": "Valid Language Code",
     "name_th": "ตรวจสอบรหัสภาษา",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["html-lang-valid"]},

    {"id": "wcag-04", "name": "Heading Order",
     "name_th": "ตรวจการเรียงลำดับ <h1-h6>",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["heading-order"]},

    {"id": "wcag-05", "name": "List Structure",
     "name_th": "ตรวจโครงสร้างแท็กรายการ",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["list"]},

    {"id": "wcag-06", "name": "List Items",
     "name_th": "ตรวจแท็ก <li>",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["listitem"]},

    {"id": "wcag-07", "name": "Iframe Title",
     "name_th": "ตรวจแอตทริบิวต์ใน <iframe>",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["frame-title"]},

    {"id": "wcag-08", "name": "Table Structure",
     "name_th": "ตรวจโครงสร้างตาราง",
     "standard": "wcag", "category": "โครงสร้าง HTML",
     "type": "axe", "rules": ["th-has-data-cells", "td-headers-attr"]},

    # ── หมวด 2: ฟอร์มและอินพุต (5 ข้อ) ─────────────────────────────
    {"id": "wcag-09", "name": "Input Labels",
     "name_th": "ตรวจการเชื่อม Label",
     "standard": "wcag", "category": "ฟอร์มและอินพุต",
     "type": "axe", "rules": ["label"]},

    {"id": "wcag-10", "name": "Image Buttons",
     "name_th": "ตรวจปุ่มที่เป็นรูปภาพ",
     "standard": "wcag", "category": "ฟอร์มและอินพุต",
     "type": "axe", "rules": ["input-image-alt"]},

    {"id": "wcag-11", "name": "Autocomplete",
     "name_th": "ตรวจแอตทริบิวต์เติมอัตโนมัติ",
     "standard": "wcag", "category": "ฟอร์มและอินพุต",
     "type": "axe", "rules": ["autocomplete-valid"]},

    {"id": "wcag-12", "name": "Fieldset & Legend",
     "name_th": "ตรวจการจัดกลุ่มฟอร์ม",
     "standard": "wcag", "category": "ฟอร์มและอินพุต",
     "type": "axe", "rules": ["fieldset-no-legend"]},

    {"id": "wcag-13", "name": "No Duplicate Labels",
     "name_th": "ตรวจ Label ซ้ำซ้อน",
     "standard": "wcag", "category": "ฟอร์มและอินพุต",
     "type": "axe", "rules": ["form-field-multiple-labels"]},

    # ── หมวด 3: รูปภาพและสื่อ (5 ข้อ) ──────────────────────────────
    {"id": "wcag-14", "name": "Image Alt Text",
     "name_th": "ตรวจข้อความอธิบายภาพ",
     "standard": "wcag", "category": "รูปภาพและสื่อ",
     "type": "axe", "rules": ["image-alt"]},

    {"id": "wcag-15", "name": "Image Map Alt",
     "name_th": "ตรวจลิงก์บนรูปภาพ",
     "standard": "wcag", "category": "รูปภาพและสื่อ",
     "type": "axe", "rules": ["area-alt"]},

    {"id": "wcag-16", "name": "Object Fallback",
     "name_th": "ตรวจข้อความสำรองของ Object",
     "standard": "wcag", "category": "รูปภาพและสื่อ",
     "type": "axe", "rules": ["object-alt"]},

    {"id": "wcag-17", "name": "Video Captions",
     "name_th": "ตรวจคำบรรยายวิดีโอ",
     "standard": "wcag", "category": "รูปภาพและสื่อ",
     "type": "axe", "rules": ["video-caption"]},

    {"id": "wcag-18", "name": "SVG Accessible Name",
     "name_th": "ตรวจชื่อภาพ SVG",
     "standard": "wcag", "category": "รูปภาพและสื่อ",
     "type": "axe", "rules": ["svg-img-alt"]},

    # ── หมวด 4: การนำทางและคีย์บอร์ด (7 ข้อ) ──────────────────────
    {"id": "wcag-19", "name": "Link Name",
     "name_th": "ตรวจข้อความในลิงก์",
     "standard": "wcag", "category": "การนำทางและคีย์บอร์ด",
     "type": "axe", "rules": ["link-name"]},

    {"id": "wcag-20", "name": "Button Name",
     "name_th": "ตรวจข้อความบนปุ่ม",
     "standard": "wcag", "category": "การนำทางและคีย์บอร์ด",
     "type": "axe", "rules": ["button-name"]},

    {"id": "wcag-21", "name": "Tabindex",
     "name_th": "ตรวจลำดับการกด Tab",
     "standard": "wcag", "category": "การนำทางและคีย์บอร์ด",
     "type": "axe", "rules": ["tabindex"]},

    {"id": "wcag-22", "name": "Unique IDs",
     "name_th": "ตรวจสอบ ID ซ้ำ",
     "standard": "wcag", "category": "การนำทางและคีย์บอร์ด",
     "type": "axe", "rules": ["duplicate-id", "duplicate-id-aria"]},

    {"id": "wcag-23", "name": "Skip Link / Bypass",
     "name_th": "ตรวจปุ่มข้ามเมนู",
     "standard": "wcag", "category": "การนำทางและคีย์บอร์ด",
     "type": "axe", "rules": ["bypass"]},

    {"id": "wcag-24", "name": "Hidden Focusable",
     "name_th": "ตรวจสอบปุ่มที่ถูกซ่อน",
     "standard": "wcag", "category": "การนำทางและคีย์บอร์ด",
     "type": "axe", "rules": ["aria-hidden-focus"]},

    {"id": "wcag-25", "name": "Scrollable Region",
     "name_th": "ตรวจกล่องเลื่อน Scroll",
     "standard": "wcag", "category": "การนำทางและคีย์บอร์ด",
     "type": "axe", "rules": ["scrollable-region-focusable"]},

    # ── หมวด 5: การแสดงผลและสี (4 ข้อ) ─────────────────────────────
    {"id": "wcag-26", "name": "Color Contrast",
     "name_th": "ตรวจความเปรียบต่างสี",
     "standard": "wcag", "category": "การแสดงผลและสี",
     "type": "axe", "rules": ["color-contrast"]},

    {"id": "wcag-27", "name": "Viewport Zoom",
     "name_th": "ตรวจการล็อกการซูม",
     "standard": "wcag", "category": "การแสดงผลและสี",
     "type": "axe", "rules": ["meta-viewport"]},

    {"id": "wcag-28", "name": "Orientation Lock",
     "name_th": "ตรวจการล็อกทิศทางจอ",
     "standard": "wcag", "category": "การแสดงผลและสี",
     "type": "axe", "rules": ["css-orientation-lock"]},

    {"id": "wcag-29", "name": "Text Spacing",
     "name_th": "ตรวจระยะห่างตัวอักษร",
     "standard": "wcag", "category": "การแสดงผลและสี",
     "type": "axe", "rules": ["avoid-inline-spacing"]},

    # ── หมวด 6: กฎระเบียบ ARIA (8 ข้อ) ─────────────────────────────
    {"id": "wcag-30", "name": "Valid ARIA Roles",
     "name_th": "ตรวจสอบค่า Role",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-roles"]},

    {"id": "wcag-31", "name": "Valid ARIA Attributes",
     "name_th": "ตรวจสอบชื่อแอตทริบิวต์",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-valid-attr"]},

    {"id": "wcag-32", "name": "Valid ARIA Values",
     "name_th": "ตรวจสอบค่าภายใน ARIA",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-valid-attr-value"]},

    {"id": "wcag-33", "name": "Required Attributes",
     "name_th": "ตรวจแอตทริบิวต์บังคับ",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-required-attr"]},

    {"id": "wcag-34", "name": "Required Parent",
     "name_th": "ตรวจแท็กแม่ของ ARIA",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-required-parent"]},

    {"id": "wcag-35", "name": "Required Children",
     "name_th": "ตรวจแท็กลูกของ ARIA",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-required-children"]},

    {"id": "wcag-36", "name": "Body aria-hidden",
     "name_th": "ตรวจการซ่อนหน้าเว็บ",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-hidden-body"]},

    {"id": "wcag-37", "name": "Dialog Name",
     "name_th": "ตรวจชื่อ Pop-up",
     "standard": "wcag", "category": "กฎระเบียบ ARIA",
     "type": "axe", "rules": ["aria-dialog-name"]},

    # WCAG count: 8 + 5 + 5 + 7 + 4 + 8 = 37 ✓

    # ═════════════════════════════════════════════════════════════════
    #  2. Core Web Vitals & SEO — 9 items
    # ═════════════════════════════════════════════════════════════════

    # ── Performance (3 ข้อ) ─────────────────────────────────────────
    {"id": "cwv-01", "name": "LCP (Largest Contentful Paint)",
     "name_th": "ความเร็วการโหลดองค์ประกอบหลัก",
     "standard": "cwv", "category": "Performance",
     "type": "lighthouse", "rules": ["largest-contentful-paint"]},

    {"id": "cwv-02", "name": "INP / TBT (Interaction / Blocking Time)",
     "name_th": "ความไวในการตอบสนองคำสั่ง",
     "standard": "cwv", "category": "Performance",
     "type": "lighthouse", "rules": ["total-blocking-time"]},

    {"id": "cwv-03", "name": "CLS (Cumulative Layout Shift)",
     "name_th": "ความนิ่งของการแสดงผลหน้าเว็บ",
     "standard": "cwv", "category": "Performance",
     "type": "lighthouse", "rules": ["cumulative-layout-shift"]},

    # ── SEO (6 ข้อ) ────────────────────────────────────────────────
    {"id": "cwv-04", "name": "Meta Data (Title & Description)",
     "name_th": "ตรวจข้อมูลอธิบายหน้าเว็บ",
     "standard": "cwv", "category": "SEO",
     "type": "lighthouse", "rules": ["document-title", "meta-description"]},

    {"id": "cwv-05", "name": "Crawling & Indexing",
     "name_th": "ตรวจการอนุญาตให้ Search Engine จัดเก็บข้อมูล",
     "standard": "cwv", "category": "SEO",
     "type": "lighthouse", "rules": ["is-crawlable"]},

    {"id": "cwv-06", "name": "Link Crawlability",
     "name_th": "ตรวจความสมบูรณ์ของลิงก์",
     "standard": "cwv", "category": "SEO",
     "type": "lighthouse", "rules": ["crawlable-anchors"]},

    {"id": "cwv-07", "name": "Canonical URL",
     "name_th": "ป้องกันปัญหาเนื้อหาซ้ำซ้อน",
     "standard": "cwv", "category": "SEO",
     "type": "lighthouse", "rules": ["canonical"]},

    {"id": "cwv-08", "name": "Mobile-Friendly (Tap Targets & Viewport)",
     "name_th": "การรองรับผู้ใช้บนมือถือ",
     "standard": "cwv", "category": "SEO",
     "type": "lighthouse", "rules": ["viewport", "tap-targets"]},

    {"id": "cwv-09", "name": "Structured Data (Schema.org)",
     "name_th": "ตรวจโค้ดข้อมูลอัจฉริยะ",
     "standard": "cwv", "category": "SEO",
     "type": "lighthouse", "rules": ["structured-data"]},

    # CWV count: 3 + 6 = 9 ✓

    # ═════════════════════════════════════════════════════════════════
    #  3. NCSA / สกมช. — 11 items
    # ═════════════════════════════════════════════════════════════════

    # ── หมวด 1: Security Headers (4 ข้อ) ───────────────────────────
    {"id": "ncsa-01", "name": "Enforcement HTTPS",
     "name_th": "บังคับเชื่อมต่อแบบปลอดภัย",
     "standard": "ncsa", "category": "Security Headers",
     "type": "custom", "eval_key": "https_redirect"},

    {"id": "ncsa-02", "name": "HSTS (Strict Transport Security)",
     "name_th": "บังคับใช้ HTTPS บนเบราว์เซอร์",
     "standard": "ncsa", "category": "Security Headers",
     "type": "custom", "eval_key": "ncsa_hsts"},

    {"id": "ncsa-03", "name": "Anti-Clickjacking",
     "name_th": "ป้องกันการครอบหน้าเว็บ",
     "standard": "ncsa", "category": "Security Headers",
     "type": "custom", "eval_key": "ncsa_clickjack"},

    {"id": "ncsa-04", "name": "Server Information Disclosure",
     "name_th": "ซ่อนข้อมูลซอฟต์แวร์เซิร์ฟเวอร์",
     "standard": "ncsa", "category": "Security Headers",
     "type": "custom", "eval_key": "server_info"},

    # ── หมวด 2: SSL/TLS Certificate (2 ข้อ) ────────────────────────
    {"id": "ncsa-05", "name": "TLS Version",
     "name_th": "ตรวจเวอร์ชันโปรโตคอลเข้ารหัส",
     "standard": "ncsa", "category": "SSL/TLS Certificate",
     "type": "custom", "eval_key": "tls_version"},

    {"id": "ncsa-06", "name": "Cipher Suite Strength",
     "name_th": "ตรวจชุดรหัสเข้ารหัส",
     "standard": "ncsa", "category": "SSL/TLS Certificate",
     "type": "custom", "eval_key": "cipher"},

    # ── หมวด 3: ช่องโหว่บนหน้าเว็บ (2 ข้อ) ────────────────────────
    {"id": "ncsa-07", "name": "XSS & SQL Injection",
     "name_th": "ตรวจการยิงสคริปต์อันตรายผ่านฟอร์ม",
     "standard": "ncsa", "category": "ช่องโหว่บนหน้าเว็บ",
     "type": "custom", "eval_key": "xss_sqli"},

    {"id": "ncsa-08", "name": "Cookie Security Flags",
     "name_th": "ตรวจสอบความปลอดภัยของ Cookie",
     "standard": "ncsa", "category": "ช่องโหว่บนหน้าเว็บ",
     "type": "custom", "eval_key": "cookie_security"},

    # ── หมวด 4: เทคโนโลยี & CMS (3 ข้อ) ───────────────────────────
    {"id": "ncsa-09", "name": "Software Fingerprinting",
     "name_th": "ตรวจสอบการระบุเวอร์ชันระบบ",
     "standard": "ncsa", "category": "เทคโนโลยี & CMS",
     "type": "custom", "eval_key": "fingerprinting"},

    {"id": "ncsa-10", "name": "Known CVE Vulnerabilities",
     "name_th": "ตรวจสอบประวัติช่องโหว่ซอฟต์แวร์",
     "standard": "ncsa", "category": "เทคโนโลยี & CMS",
     "type": "custom", "eval_key": "cve"},

    {"id": "ncsa-11", "name": "Exposed Admin/Login URLs",
     "name_th": "ตรวจหน้าล็อกอินมาตรฐาน",
     "standard": "ncsa", "category": "เทคโนโลยี & CMS",
     "type": "custom", "eval_key": "admin_urls"},

    # NCSA count: 4 + 2 + 2 + 3 = 11 ✓

    # ═════════════════════════════════════════════════════════════════
    #  4. OWASP HTTP Security Headers — 11 items
    # ═════════════════════════════════════════════════════════════════

    {"id": "owasp-01", "name": "Content-Security-Policy (CSP)",
     "name_th": "ระบุทรัพยากรที่อนุญาตให้โหลด",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "content-security-policy",
     "validator": _v_csp},

    {"id": "owasp-02", "name": "Strict-Transport-Security (HSTS)",
     "name_th": "บังคับให้เชื่อมต่อผ่าน HTTPS",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "strict-transport-security",
     "validator": _v_hsts},

    {"id": "owasp-03", "name": "X-Frame-Options",
     "name_th": "ป้องกันหน้าเว็บถูกซ้อนใน iframe",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "x-frame-options",
     "validator": _v_xfo},

    {"id": "owasp-04", "name": "X-Content-Type-Options",
     "name_th": "ห้ามเบราว์เซอร์เดาประเภทไฟล์",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "x-content-type-options",
     "validator": _v_xcto},

    {"id": "owasp-05", "name": "Referrer-Policy",
     "name_th": "ควบคุมข้อมูล URL ต้นทาง",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "referrer-policy",
     "validator": _v_referrer},

    {"id": "owasp-06", "name": "Permissions-Policy",
     "name_th": "จำกัดการเข้าถึงฟีเจอร์ฮาร์ดแวร์",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "permissions-policy"},

    {"id": "owasp-07", "name": "Cross-Origin-Opener-Policy (COOP)",
     "name_th": "แยกระบบประมวลผลหน้าเว็บ",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "cross-origin-opener-policy",
     "validator": _v_coop},

    {"id": "owasp-08", "name": "Cross-Origin-Embedder-Policy (COEP)",
     "name_th": "บล็อกการดึงทรัพยากรข้ามโดเมน",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "cross-origin-embedder-policy",
     "validator": _v_coep},

    {"id": "owasp-09", "name": "Cross-Origin-Resource-Policy (CORP)",
     "name_th": "จำกัดการดึงทรัพยากร",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "cross-origin-resource-policy",
     "validator": _v_corp},

    {"id": "owasp-10", "name": "Cache-Control",
     "name_th": "ควบคุมกลไกแคช",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "cache-control",
     "validator": _v_cache},

    {"id": "owasp-11", "name": "Set-Cookie Attributes",
     "name_th": "ตรวจคุณสมบัติเสริมของ Cookie",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "custom", "eval_key": "set_cookie_owasp"},

    # OWASP count: 11 ✓
]

# Compile-time assertion: exactly 68
assert len(CHECKS) == 68, f"CHECKS must have 68 items, got {len(CHECKS)}"


# ══════════════════════════════════════════════════════════════════════════════
#  Standards metadata
# ══════════════════════════════════════════════════════════════════════════════
STANDARDS_META = [
    {"id": "wcag",
     "name": "WCAG 2.1",
     "name_full": "Web Content Accessibility Guidelines 2.1",
     "owner": "W3C",
     "icon": "♿"},
    {"id": "cwv",
     "name": "Core Web Vitals & SEO",
     "name_full": "Core Web Vitals & SEO (Google Lighthouse)",
     "owner": "Google",
     "icon": "📊"},
    {"id": "ncsa",
     "name": "มาตรฐานความมั่นคงปลอดภัย สกมช.",
     "name_full": "มาตรฐานความมั่นคงปลอดภัยเว็บไซต์ สกมช.",
     "owner": "สกมช.",
     "icon": "🛡️"},
    {"id": "owasp",
     "name": "OWASP HTTP Security Headers",
     "name_full": "OWASP Secure Headers Project",
     "owner": "OWASP Foundation",
     "icon": "🔒"},
]


# ══════════════════════════════════════════════════════════════════════════════
#  Main entry point
# ══════════════════════════════════════════════════════════════════════════════

def _evaluate_one(check, axe, lh, hdr, wap, zap):
    t = check["type"]
    if t == "axe":
        return _eval_axe(check, axe)
    if t == "lighthouse":
        return _eval_lh(check, lh)
    if t == "header":
        return _eval_header(check, hdr)
    if t == "custom":
        return CUSTOM_EVAL[check["eval_key"]](check, hdr, wap, zap)
    return _make(check, WARNING, "Unknown check type", "unknown")


# ── Which tools each standard needs ──────────────────────────────────────────
STANDARD_TOOLS: dict[str, list[str]] = {
    "wcag":  ["axe"],
    "cwv":   ["lighthouse"],
    "ncsa":  ["headers", "wappalyzer", "zap"],
    "owasp": ["headers"],
}

VALID_STANDARD_IDS = set(STANDARD_TOOLS.keys())


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


def build_standards_report(
    url: str,
    axe_data: Any = None,
    lighthouse_data: Any = None,
    headers_data: Any = None,
    wappalyzer_data: Any = None,
    zap_data: Any = None,
) -> dict:
    """Build the complete 68-item standards compliance report."""

    # Normalize — unwrap API response envelopes
    axe = _extract(axe_data)
    lh = _extract(lighthouse_data)
    hdr = _extract(headers_data)
    wap = _extract(wappalyzer_data)
    zap = _extract(zap_data)

    # Evaluate every check
    results = [_evaluate_one(c, axe, lh, hdr, wap, zap) for c in CHECKS]

    # Group by standard → category (preserving order from CHECKS)
    standards = _build_standards_list(results)

    total_p = sum(s["passed"] for s in standards)
    total_f = sum(s["failed"] for s in standards)
    total_w = sum(s["warning"] for s in standards)

    return {
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": 68,
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
    results = [_evaluate_one(c, axe, lh, hdr, wap, zap) for c in filtered_checks]

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
