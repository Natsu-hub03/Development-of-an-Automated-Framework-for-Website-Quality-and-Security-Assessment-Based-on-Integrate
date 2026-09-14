"""
Master checklist data — exactly 71 items across 4 web standards.

This module contains pure data definitions only:
- CHECKS: The 71 checklist items with their rules, types, and metadata
- STANDARDS_META: Display metadata for each standard
- STANDARD_TOOLS: Which scanner tools each standard requires
- VALID_STANDARD_IDS: Set of valid standard identifiers
"""

from services.standards.evaluators import (
    _v_csp, _v_hsts, _v_xfo, _v_xcto,
    _v_referrer, _v_coop, _v_coep, _v_corp, _v_cache,
    _v_xpcdp, _v_clear_site_data, _v_xxssp,
)


# ══════════════════════════════════════════════════════════════════════════════
#  Master Checklist — exactly 71 items
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
    #  4. OWASP HTTP Security Headers — 14 items
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

    {"id": "owasp-12", "name": "X-Permitted-Cross-Domain-Policies",
     "name_th": "ห้าม Flash/PDF โหลดข้อมูลข้ามโดเมน",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "x-permitted-cross-domain-policies",
     "validator": _v_xpcdp},

    {"id": "owasp-13", "name": "Clear-Site-Data",
     "name_th": "ล้างข้อมูล Browser เมื่อ Logout",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "clear-site-data",
     "validator": _v_clear_site_data},

    {"id": "owasp-14", "name": "X-XSS-Protection",
     "name_th": "ปิด XSS Auditor เก่าของเบราว์เซอร์",
     "standard": "owasp", "category": "HTTP Security Headers",
     "type": "header", "header": "x-xss-protection",
     "validator": _v_xxssp},

    # OWASP count: 14 ✓
]

# Compile-time assertion: exactly 71
assert len(CHECKS) == 71, f"CHECKS must have 71 items, got {len(CHECKS)}"


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


# ── Which tools each standard needs ──────────────────────────────────────────
STANDARD_TOOLS: dict[str, list[str]] = {
    "wcag":  ["axe"],
    "cwv":   ["lighthouse"],
    "ncsa":  ["headers", "wappalyzer", "zap"],
    "owasp": ["headers"],
}

VALID_STANDARD_IDS = set(STANDARD_TOOLS.keys())
