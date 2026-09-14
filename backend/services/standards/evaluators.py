"""
Evaluators for each check type: axe-core, Lighthouse, HTTP headers, and custom.

Each evaluator takes a check definition dict and scanner data, returning a
result dict with status, detail, evidence, etc.
"""

from typing import Optional

from services.standards.helpers import (
    PASS, FAIL, WARNING,
    WEAK_CIPHERS, ADMIN_PATHS,
    _make,
)
from services.standards.i18n import RULE_FAIL_TH, RULE_PASS_TH


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


def _v_xpcdp(val):
    v = val.strip().lower()
    if v == "none":
        return PASS, f"X-Permitted-Cross-Domain-Policies: {val}"
    return WARNING, f"X-Permitted-Cross-Domain-Policies ควรเป็น 'none': {val}"


def _v_clear_site_data(val):
    # Presence is sufficient; value should contain at least one directive
    if val.strip():
        return PASS, f"Clear-Site-Data: {val[:120]}"
    return WARNING, "Clear-Site-Data header ว่างเปล่า"


def _v_xxssp(val):
    v = val.strip()
    if v == "0":
        return PASS, "X-XSS-Protection: 0 (ปิด XSS Auditor ตามแนว OWASP)"
    return WARNING, \
        f"X-XSS-Protection ควรเป็น '0' เพื่อปิด XSS Auditor เก่า: {val}"


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


def evaluate_one(check, axe, lh, hdr, wap, zap):
    """Dispatch a single check to the appropriate evaluator."""
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
