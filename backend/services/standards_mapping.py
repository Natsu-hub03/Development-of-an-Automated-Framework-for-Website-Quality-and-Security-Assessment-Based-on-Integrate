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


# ── Status constants ──────────────────────────────────────────────────────────
PASS = "pass"
FAIL = "fail"
WARNING = "warning"
INFO = "info"

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
    return {
        "id": check["id"],
        "name": check["name"],
        "name_th": check["name_th"],
        "standard": check["standard"],
        "category": check["category"],
        "status": status,
        "detail": detail,
        "source_tool": source,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Evaluators: axe-core, Lighthouse, header, custom
# ══════════════════════════════════════════════════════════════════════════════

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
        for v in violations:
            if v["id"] in failed:
                cnt = v.get("nodes_count", 1)
                details.append(f'{v.get("help", v["id"])} (พบ {cnt} จุด)')
        return _make(check, FAIL, "; ".join(details), "axe-core")

    if warned:
        details = []
        for i in incomplete:
            if i["id"] in warned:
                details.append(i.get("help", i["id"]))
        return _make(check, WARNING,
                     "ต้องตรวจสอบเพิ่ม: " + "; ".join(details), "axe-core")

    return _make(check, PASS, "ผ่านการตรวจสอบ", "axe-core")


def _eval_lh(check: dict, lh_data: Optional[dict]) -> dict:
    """Evaluate check against Lighthouse failed audits."""
    if not lh_data:
        return _make(check, WARNING, "ยังไม่ได้รัน Lighthouse scan", "lighthouse")

    audit_ids = check["rules"]
    failed_audits = lh_data.get("failed_audits", [])
    failed_map = {a["id"]: a for a in failed_audits}

    failures = []
    for aid in audit_ids:
        if aid in failed_map:
            a = failed_map[aid]
            dv = a.get("displayValue", "")
            sc = a.get("score", "?")
            failures.append(
                f'{a.get("title", aid)} (score: {sc}{", " + dv if dv else ""})')

    if failures:
        worst = min(
            (failed_map[aid]["score"]
             for aid in audit_ids if aid in failed_map),
            default=50,
        )
        status = FAIL if worst < 50 else WARNING
        return _make(check, status, "; ".join(failures), "lighthouse")

    return _make(check, PASS, "ผ่านการตรวจสอบ", "lighthouse")


def _eval_header(check: dict, headers_data: Optional[dict]) -> dict:
    """Evaluate OWASP header check — presence + optional value validation."""
    if not headers_data:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")

    header_key = check["header"]
    sec_headers = headers_data.get("security_headers", {})
    value = sec_headers.get(header_key)

    if not value:
        return _make(check, FAIL,
                     f"ไม่พบ Header: {header_key}", "headers-scan")

    validator = check.get("validator")
    if validator:
        status, detail = validator(value)
        return _make(check, status, detail, "headers-scan")

    return _make(check, PASS, f"{header_key}: {value}", "headers-scan")


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
        return _make(check, PASS,
                     "HTTPS บังคับใช้ — HTTP redirect ไปยัง HTTPS",
                     "headers-scan")
    if is_https:
        if redir.get("checked") and not redir.get("redirects_to_https"):
            return _make(check, WARNING,
                         "ใช้ HTTPS แต่ HTTP ไม่ redirect ไปยัง HTTPS",
                         "headers-scan")
        return _make(check, PASS, "เว็บไซต์ใช้ HTTPS", "headers-scan")
    return _make(check, FAIL, "เว็บไซต์ไม่ได้ใช้ HTTPS", "headers-scan")


def _eval_ncsa_hsts(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    val = hdr.get("security_headers", {}).get("strict-transport-security")
    if not val:
        return _make(check, FAIL,
                     "ไม่พบ Strict-Transport-Security header", "headers-scan")
    return _make(check, PASS, f"HSTS: {val}", "headers-scan")


def _eval_ncsa_clickjack(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    h = hdr.get("security_headers", {})
    xfo = h.get("x-frame-options")
    csp = h.get("content-security-policy", "") or ""

    if xfo:
        v = xfo.upper()
        if "DENY" in v or "SAMEORIGIN" in v:
            return _make(check, PASS,
                         f"X-Frame-Options: {xfo}", "headers-scan")
    if "frame-ancestors" in csp.lower():
        return _make(check, PASS,
                     f"CSP frame-ancestors: {csp[:100]}", "headers-scan")
    return _make(check, FAIL,
                 "ไม่พบการป้องกัน Clickjacking "
                 "(X-Frame-Options หรือ CSP frame-ancestors)",
                 "headers-scan")


def _eval_server_info(check, hdr, wap, zap):
    if not hdr:
        return _make(check, INFO, "ไม่มีข้อมูล headers scan", "headers-scan")
    si = hdr.get("server_info", {})
    server = si.get("server")
    xpb = si.get("x-powered-by")
    issues = []
    if server:
        issues.append(f"Server: {server}")
    if xpb:
        issues.append(f"X-Powered-By: {xpb}")
    if not issues:
        return _make(check, PASS,
                     "ไม่พบการเปิดเผยข้อมูลเซิร์ฟเวอร์", "headers-scan")
    return _make(check, WARNING,
                 "เปิดเผยข้อมูลเซิร์ฟเวอร์: " + ", ".join(issues),
                 "headers-scan")


def _eval_tls_version(check, hdr, wap, zap):
    if not hdr:
        return _make(check, INFO, "ไม่มีข้อมูล headers scan", "headers-scan")
    tls_info = hdr.get("tls")
    if not tls_info or tls_info.get("error"):
        err = tls_info.get("error", "ไม่มีข้อมูล") if tls_info else "ไม่มีข้อมูล"
        return _make(check, WARNING,
                     f"ไม่สามารถตรวจ TLS: {err}", "headers-scan")
    proto = tls_info.get("protocol", "")
    if proto in ("TLSv1.3", "TLSv1.2"):
        return _make(check, PASS,
                     f"TLS Protocol: {proto}", "headers-scan")
    if proto in ("TLSv1.1", "TLSv1.0", "SSLv3"):
        return _make(check, FAIL,
                     f"TLS Protocol ไม่ปลอดภัย: {proto} (ต้อง TLS 1.2+)",
                     "headers-scan")
    return _make(check, WARNING,
                 f"TLS Protocol: {proto or 'ไม่ทราบ'}", "headers-scan")


def _eval_cipher(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    tls_info = hdr.get("tls")
    if not tls_info or tls_info.get("error"):
        return _make(check, WARNING, "ไม่สามารถตรวจ Cipher Suite", "headers-scan")
    cipher = (tls_info.get("cipher_name")
              or tls_info.get("cipher_standard_name", ""))
    if not cipher:
        return _make(check, WARNING, "ไม่ทราบ Cipher Suite", "headers-scan")
    upper = cipher.upper()
    if any(wc in upper for wc in WEAK_CIPHERS):
        return _make(check, FAIL,
                     f"Cipher Suite ไม่ปลอดภัย: {cipher}", "headers-scan")
    return _make(check, PASS, f"Cipher Suite: {cipher}", "headers-scan")


def _eval_xss_sqli(check, hdr, wap, zap):
    if not zap:
        return _make(check, WARNING,
                     "ต้องรัน ZAP scan เพื่อตรวจ XSS/SQL Injection", "zap")
    alerts = zap.get("alerts", [])
    keywords = ["xss", "sql injection", "cross-site scripting", "injection"]
    xss_sqli = [
        a for a in alerts
        if a.get("risk") in ("High", "Medium")
        and any(kw in a.get("alert", "").lower() for kw in keywords)
    ]
    if xss_sqli:
        names = list(set(a["alert"] for a in xss_sqli))[:3]
        return _make(check, FAIL,
                     f"พบช่องโหว่: {', '.join(names)}", "zap")
    return _make(check, PASS,
                 "ไม่พบช่องโหว่ XSS/SQL Injection จาก ZAP scan", "zap")


def _eval_cookie_security(check, hdr, wap, zap):
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    cookie_info = hdr.get("cookies", {})
    if not cookie_info.get("has_cookies"):
        return _make(check, PASS,
                     "ไม่พบ Cookie ที่ต้องตรวจสอบ", "headers-scan")
    cookies = cookie_info.get("cookies", [])
    issues = []
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
            issues.append(f'{name}: ขาด {", ".join(missing)}')
    if issues:
        return _make(check, FAIL, "; ".join(issues[:3]), "headers-scan")
    return _make(check, PASS,
                 "Cookie มี Security Flags ครบถ้วน", "headers-scan")


def _eval_fingerprinting(check, hdr, wap, zap):
    if not wap:
        return _make(check, WARNING, "ยังไม่ได้รัน Wappalyzer scan", "wappalyzer")
    techs = wap.get("technologies", [])
    versioned = [t for t in techs if t.get("version")]
    if versioned:
        names = [f'{t["name"]} v{t["version"]}' for t in versioned[:5]]
        return _make(check, WARNING,
                     f"พบเวอร์ชันซอฟต์แวร์เปิดเผย: {', '.join(names)}",
                     "wappalyzer")
    return _make(check, PASS,
                 "ไม่พบการเปิดเผยเวอร์ชันซอฟต์แวร์", "wappalyzer")


def _eval_cve(check, hdr, wap, zap):
    if not wap:
        return _make(check, WARNING, "ยังไม่ได้รัน Wappalyzer scan", "wappalyzer")
    techs = wap.get("technologies", [])
    versioned = [t for t in techs if t.get("version")]
    if versioned:
        names = [f'{t["name"]} v{t["version"]}' for t in versioned[:3]]
        return _make(check, WARNING,
                     f"พบเวอร์ชัน — ควรตรวจ CVE: {', '.join(names)}",
                     "wappalyzer")
    return _make(check, PASS,
                 "ไม่พบเวอร์ชันที่ต้องตรวจสอบ CVE", "wappalyzer")


def _eval_admin_urls(check, hdr, wap, zap):
    if not zap:
        return _make(check, WARNING,
                     "ต้องรัน ZAP scan เพื่อตรวจ Admin URLs", "zap")
    alerts = zap.get("alerts", [])
    found = set()
    for a in alerts:
        url_str = a.get("url", "").lower()
        for path in ADMIN_PATHS:
            if path in url_str:
                found.add(path)
    if found:
        return _make(check, WARNING,
                     f"พบ URL ที่อาจเป็นหน้าจัดการ: {', '.join(sorted(found))}",
                     "zap")
    return _make(check, PASS,
                 "ไม่พบ Admin/Login URL ที่เปิดเผย", "zap")


def _eval_set_cookie_owasp(check, hdr, wap, zap):
    """OWASP Set-Cookie — stricter than NCSA, includes Expires/Max-Age."""
    if not hdr:
        return _make(check, WARNING, "ยังไม่ได้รัน headers scan", "headers-scan")
    cookie_info = hdr.get("cookies", {})
    if not cookie_info.get("has_cookies"):
        return _make(check, PASS, "ไม่พบ Set-Cookie header", "headers-scan")
    cookies = cookie_info.get("cookies", [])
    issues = []
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
            issues.append(f'{name}: ขาด {", ".join(missing)}')
    if issues:
        return _make(check, FAIL, "; ".join(issues[:3]), "headers-scan")
    return _make(check, PASS,
                 "Set-Cookie มี Attributes ครบถ้วน", "headers-scan")


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
            cat_map[cat].append({
                "id": c["id"],
                "name": c["name"],
                "name_th": c["name_th"],
                "status": c["status"],
                "detail": c["detail"],
                "source_tool": c["source_tool"],
            })

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
