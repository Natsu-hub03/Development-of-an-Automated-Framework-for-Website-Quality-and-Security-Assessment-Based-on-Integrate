"""
check_sites_reachable.py
ตรวจสอบความพร้อมในการเข้าถึงเว็บไซต์ 600 เว็บอย่างสมบูรณ์แบบ (Production-Grade Accuracy)
จำลองพฤติกรรมของ Modern Browser (Chrome):
- HTTPS-First: ลองเชื่อมต่อผ่าน HTTPS ก่อนเสมอ
- Automatic Redirect: วิ่งตาม Meta Refresh, Header Refresh และ JavaScript window.location
- Cloudflare WAF: แยกแยะ 403 ของ Cloudflare Bot Challenge ออกจาก 403 ที่เซิร์ฟเวอร์ตายจริง
- DNS Fallback: หาก ISP บล็อก DNS จะใช้ Google DNS (DoH) ตรวจสอบความมีอยู่จริงของโดเมน
- Content Validation: คัดกรองหน้าจอขาว, Fatal Error, PHP Warning, Database Crash, โดเมนหมดอายุ
Export เป็น reachability_report.xlsx ลิงก์ทุกแถวสามารถคลิกเปิดดูได้ทันที
"""
import sys
import time
import ssl
import json
import socket
import re
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from collections import Counter

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    print("[!] ต้องติดตั้ง openpyxl ก่อน: pip install openpyxl")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "standards_score_results.xlsx"
OUTPUT_PATH = BASE_DIR / "reachability_report.xlsx"

MAX_WORKERS = 25
TIMEOUT = 12

REAL_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ข้อความ Error ใน Body ที่บ่งบอกว่าเว็บพังจริงๆ
FATAL_PATTERNS = [
    b"fatal error:",
    b"parse error:",
    b"uncaught error:",
    b"uncaught exception:",
    b"call to a member function",
    b"unknown mysql server host",
    b"connect failed:",
    b"sqlstate[",
    b"mysql_connect(): access denied",
    b"pg_connect(): unable to connect",
    b"no space left on device",
    b"failed to open stream: permission denied",
    b"error establishing a database connection",
    b"a database error occurred",
    b"page cannot be displayed",
    b"warning: session_start()",
    b"warning: mysqli::",
    b"warning: mysql_",
]

# ข้อความหรือ Title ที่บ่งบอกว่าเว็บนี้ไม่มีหน้าจริง / เป็นหน้าขายโดเมน
PARKED_PATTERNS = [
    b"<title>domain default page</title>",
    b"/cgi-sys/defaultwebpage.cgi",
    b"assets.abovedomains.com",
    b"forsale.min.js",
    b"window.location.href=\"/lander\"",
    b"window.location.href = \"/lander\"",
    b"<title>index of /</title>",
    b"<title>iis windows server</title>",
    b"buy this domain",
    b"this domain is for sale",
    b"parkingcrew.net",
    b"sedo.com",
    b"sedoparking",
    b"namebright - coming soon",
    b"cmp_cdid",
    b"<title>namebright",
]

# ข้อความ Error บน Title ที่แสดงว่าหน้าเว็บพังหรือไม่มีอยู่
SOFT_404_TITLES = [
    b"<title>404 not found",
    b"<title>404 - not found",
    b"<title>page not found",
    b"<title>403 forbidden",
    b"<title>access denied</title>",
    b"<title>error</title>",
    b"<title>oops, an error occurred!</title>",
    b"<title>server error</title>",
]


def check_google_doh(domain: str) -> bool:
    """ตรวจผ่าน Google DNS over HTTPS ว่าโดเมนมีตัวตนอยู่จริงหรือไม่"""
    try:
        url = f"https://dns.google/resolve?name={domain}&type=A"
        req = urllib.request.Request(url, headers={"User-Agent": REAL_UA})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=5, context=ctx) as r:
            data = json.loads(r.read())
            answers = data.get("Answer", [])
            return len(answers) > 0
    except Exception:
        return False


def extract_redirect(url: str, body: bytes, headers: dict) -> str:
    """แกะหา URL ปลายทางจาก Refresh header, Meta refresh tag หรือ window.location JS"""
    refresh = headers.get("Refresh") or headers.get("refresh")
    if refresh:
        m = re.search(r"url=([^;,\s]+)", refresh, re.I)
        if m:
            return urllib.parse.urljoin(url, m.group(1).strip("'\""))

    text = body[:4096].decode("utf-8", errors="ignore")

    m = re.search(r'<meta[^>]+http-equiv=[\'"]?refresh[\'"]?[^>]+content=[\'"]?[0-9\s]*;\s*url=([^"\'\s>]+)', text, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=[\'"]?[0-9\s]*;\s*url=([^"\'\s>]+)[\'"]?[^>]+http-equiv=[\'"]?refresh[\'"]?', text, re.I)
    if m:
        return urllib.parse.urljoin(url, m.group(1).strip("'\""))

    m = re.search(r'window\.location(?:\.href)?\s*=\s*[\'"]([^\'"]+)[\'"]', text, re.I)
    if m:
        return urllib.parse.urljoin(url, m.group(1).strip("'\""))

    return ""


def try_request(url: str, timeout: int = 12) -> dict:
    """ส่ง GET request ไปยัง URL เดี่ยว"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, method="GET", headers={
        "User-Agent": REAL_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "th,en-US;q=0.9,en;q=0.8",
    })

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = resp.getcode()
            final_url = resp.geturl()
            try:
                body = resp.read(65536)
            except Exception:
                body = b""
            return {
                "status_code": status,
                "body": body,
                "final_url": final_url,
                "headers": dict(resp.headers),
                "error": None,
            }
    except urllib.error.HTTPError as e:
        final_url = url
        try:
            body = e.read(65536)
        except Exception:
            body = b""
        return {
            "status_code": e.code,
            "body": body,
            "final_url": final_url,
            "headers": dict(e.headers) if hasattr(e, "headers") else {},
            "error": f"HTTP {e.code}: {e.reason}",
        }


def check_url(url: str) -> dict:
    """
    ตรวจสอบสถานะเว็บไซต์ 1 เว็บไซต์แบบละเอียด:
    1. ลอง HTTPS ก่อนเสมอ (HTTPS-First)
    2. วิ่งตาม Meta Refresh / JS Redirect (สูงสุด 3 ทอด)
    3. ตรวจจับ Cloudflare WAF
    4. ตรวจจับ DNS ด้วย Google DoH หาก ISP บล็อก
    """
    # จัดเตรียมลำดับ URL ที่จะลอง (HTTPS ก่อน)
    urls_to_try = []
    clean_u = url.strip()
    if clean_u.startswith("https://"):
        urls_to_try.append(clean_u)
        urls_to_try.append(clean_u.replace("https://", "http://", 1))
    elif clean_u.startswith("http://"):
        urls_to_try.append(clean_u.replace("http://", "https://", 1))
        urls_to_try.append(clean_u)
    else:
        urls_to_try.append("https://" + clean_u)
        urls_to_try.append("http://" + clean_u)

    start = time.perf_counter()
    last_error = ""
    last_status = None
    dns_failed = False

    for try_url in urls_to_try:
        current_url = try_url
        redirect_hops = 0

        # ทำงานแบบ Loop ตาม Redirect สูงสุด 3 ครั้ง
        while redirect_hops < 3:
            try:
                res = try_request(current_url, timeout=TIMEOUT)
                status = res["status_code"]
                body = res["body"]
                final_url = res["final_url"]
                headers = res["headers"]
                body_lower = body.lower()

                # ถ้าเป็น placeholder ของ IIS/Nginx default บน http แต่ https มีเว็บจริง ให้ข้ามไปลอง https
                if status == 200 and current_url.startswith("http://"):
                    if b"<title>iis windows server</title>" in body_lower or b"<title>welcome to nginx!" in body_lower:
                        break

                # 1. เช็คคำสั่งดีดหน้า (Meta Refresh / JS Location / Header Refresh)
                redirect_target = extract_redirect(final_url, body, headers)
                if redirect_target and redirect_target != current_url and redirect_target != final_url:
                    current_url = redirect_target
                    redirect_hops += 1
                    continue

                elapsed = round(time.perf_counter() - start, 2)

                # 2. เช็ค Cloudflare Turnstile / WAF (ตอบ 403 หรือ 503 แต่คนเปิดได้จริง)
                if status in [403, 503] and (
                    b"challenges.cloudflare.com" in body_lower
                    or b"<title>just a moment...</title>" in body_lower
                    or b"cf-browser-verification" in body_lower
                    or "cloudflare" in headers.get("Server", "").lower()
                ):
                    return {
                        "reachable": True,
                        "status_code": status,
                        "final_url": final_url,
                        "note": "เข้าได้ (มี Cloudflare WAF)",
                        "error_type": None,
                        "error": None,
                        "duration": elapsed,
                    }

                # 3. เช็ค HTTP Status 4xx
                if status and 400 <= status < 500:
                    # ข้อยกเว้น: หากเป็น 404 แต่เนื้อหาหน้าเว็บมีขนาดใหญ่มาก (> 3000 bytes) และไม่ใช่หน้าแจ้ง 404 error
                    # แสดงว่าเป็นบั๊กของเซิร์ฟเวอร์เว็บนั้นๆ (เช่น fpo.go.th/main) ที่ส่งหน้าเว็บจริงมาพร้อมรหัส 404
                    is_soft_real_page = (
                        status == 404
                        and len(body) > 3000
                        and not any(err in body_lower for err in [b"<title>404", b"<title>not found", b"the requested url", b"<title>error</title>"])
                    )
                    if is_soft_real_page:
                        return {
                            "reachable": True,
                            "status_code": status,
                            "final_url": final_url,
                            "note": f"เข้าได้ (มีหน้าเว็บจริง แต่ Server ส่งรหัส {status})",
                            "error_type": None,
                            "error": None,
                            "duration": elapsed,
                        }

                    last_status = status
                    if status == 404:
                        last_error = "404 Not Found"
                    elif status == 403:
                        last_error = "403 Forbidden"
                    else:
                        last_error = f"HTTP {status}"
                    break

                # 4. เช็ค Fatal Server Error ใน Body
                for pat in FATAL_PATTERNS:
                    if pat in body_lower:
                        pat_str = pat.decode("utf-8", errors="replace")
                        return {
                            "reachable": False,
                            "status_code": status,
                            "final_url": final_url,
                            "error_type": "เว็บพัง (PHP/Database Error)",
                            "error": f"พบ Error: {pat_str}",
                            "duration": elapsed,
                        }

                # 5. เช็คหน้าพักโดเมน / ขายโดเมน / cPanel Default
                for pat in PARKED_PATTERNS:
                    if pat in body_lower:
                        pat_str = pat.decode("utf-8", errors="replace")
                        return {
                            "reachable": False,
                            "status_code": status,
                            "final_url": final_url,
                            "error_type": "หน้าพักโดเมน / โดเมนหมดอายุ",
                            "error": f"พบหน้าพักโดเมน: {pat_str}",
                            "duration": elapsed,
                        }

                # 6. เช็ค Soft 404 / หน้า Error เปล่าๆ
                for pat in SOFT_404_TITLES:
                    if pat in body_lower and len(body) < 3500:
                        pat_str = pat.decode("utf-8", errors="replace")
                        return {
                            "reachable": False,
                            "status_code": status,
                            "final_url": final_url,
                            "error_type": "หน้า Error / ไม่มีเนื้อหา",
                            "error": f"พบหัวข้อ Error: {pat_str}",
                            "duration": elapsed,
                        }

                # 7. เช็คหน้าจอขาว (White screen) / ไม่มีเนื้อหา (ขนาดน้อยกว่า 120 bytes และไม่มีคำสั่งดีดหน้า)
                clean_len = len(body.strip())
                if clean_len < 120 and not redirect_target:
                    return {
                        "reachable": False,
                        "status_code": status,
                        "final_url": final_url,
                        "error_type": "จอขาว / ไม่มีเนื้อหา (Blank Screen)",
                        "error": f"ขนาดเนื้อหาเพียง {clean_len} bytes",
                        "duration": elapsed,
                    }

                # 8. เช็ค HTTP Status 5xx (กรณี Server Error)
                if status and status >= 500:
                    if len(body) > 3000:
                        return {
                            "reachable": True,
                            "status_code": status,
                            "final_url": final_url,
                            "note": "เข้าได้ (Server ส่ง 500 แต่มีเนื้อหาหน้าเว็บ)",
                            "error_type": None,
                            "error": None,
                            "duration": elapsed,
                        }
                    else:
                        last_error = f"HTTP {status}"
                        last_status = status
                        break

                # 9. ผ่านเกณฑ์ทั้งหมด -> เข้าได้ปกติ
                note_str = "ปกติ (HTTP 200)"
                if redirect_hops > 0:
                    note_str = f"ปกติ (ดีดหน้าสำเร็จ ไปยัง {current_url})"

                return {
                    "reachable": True,
                    "status_code": status,
                    "final_url": current_url,
                    "note": note_str,
                    "error_type": None,
                    "error": None,
                    "duration": elapsed,
                }

            except urllib.error.URLError as e:
                reason = str(getattr(e, "reason", e))
                last_error = reason[:100]
                if "11001" in reason or "getaddrinfo failed" in reason.lower():
                    dns_failed = True
                break
            except socket.timeout:
                last_error = "Connection timed out"
                break
            except Exception as e:
                last_error = str(e)[:100]
                break

    elapsed = round(time.perf_counter() - start, 2)
    err_lower = last_error.lower()

    # ถ้าติด DNS Fail ของเน็ตบ้าน ให้ตรวจสอบผ่าน Google DoH เพิ่มเติม
    if dns_failed:
        parsed_host = urllib.parse.urlparse(url).netloc or url
        parsed_host = parsed_host.split(":")[0]
        if check_google_doh(parsed_host):
            return {
                "reachable": True,
                "status_code": 200,
                "final_url": url,
                "note": "เข้าได้ (ผ่าน Google DNS / ติดบล็อก DNS บางค่าย)",
                "error_type": None,
                "error": None,
                "duration": elapsed,
            }

    if last_status and last_status >= 500:
        error_type = f"Server Error (HTTP {last_status})"
    elif "timed out" in err_lower or "timeout" in err_lower:
        error_type = "Timeout (เว็บไม่ตอบ)"
    elif "getaddrinfo failed" in err_lower or "name or service not known" in err_lower or "nodename nor servname" in err_lower:
        error_type = "DNS Error (หาเว็บไม่เจอ)"
    elif "10061" in err_lower or "connection refused" in err_lower:
        error_type = "Connection Refused (Server ปิด)"
    elif "10054" in err_lower or "connection reset" in err_lower or "reset by peer" in err_lower:
        error_type = "Connection Reset (Server ตัดสาย)"
    elif "ssl" in err_lower or "certificate" in err_lower:
        error_type = "SSL/TLS Error"
    else:
        error_type = "การเชื่อมต่อล้มเหลว (อื่นๆ)"

    return {
        "reachable": False,
        "status_code": last_status,
        "final_url": None,
        "note": None,
        "error_type": error_type,
        "error": last_error,
        "duration": elapsed,
    }


def main():
    if not EXCEL_PATH.exists():
        print(f"[!] ไม่เจอไฟล์: {EXCEL_PATH}")
        sys.exit(1)

    print("=" * 75)
    print("  ตรวจสอบการเข้าถึงเว็บไซต์ 600 เว็บ (Production Accuracy)")
    print("  รองรับ: HTTPS-First, Meta/JS Redirect, Cloudflare WAF, DoH Fallback")
    print("=" * 75)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb["Standards Score Report"]

    sites = []
    for r in range(2, ws.max_row + 1):
        url = ws.cell(row=r, column=2).value
        if not url or str(url).strip() == "":
            continue
        category = ws.cell(row=r, column=3).value or ""
        sites.append({
            "no": len(sites) + 1,
            "row": r,
            "url": str(url).strip(),
            "category": str(category).strip(),
        })

    wb.close()
    total = len(sites)
    print(f"[*] พบทั้งหมด {total} เว็บไซต์")
    print(f"[*] ใช้ {MAX_WORKERS} Threads, Timeout {TIMEOUT}s")
    print(f"[*] เริ่มต้นการตรวจสอบ...\n")

    reachable = []
    unreachable = []
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_site = {
            executor.submit(check_url, site["url"]): site
            for site in sites
        }

        for future in as_completed(future_to_site):
            site = future_to_site[future]
            done += 1
            try:
                result = future.result()
            except Exception as e:
                result = {
                    "reachable": False, "status_code": None, "final_url": None,
                    "note": None, "error_type": "Exception", "error": str(e)[:100], "duration": 0,
                }

            site.update(result)

            icon = "✅" if result["reachable"] else "❌"
            if result["reachable"]:
                detail = result.get("note", f"HTTP {result['status_code']}")
            else:
                detail = result.get("error_type", result.get("error", ""))[:50]
            print(f"  [{done:3d}/{total}] {icon} {site['url'][:50]:50s} | {detail}")

            if result["reachable"]:
                reachable.append(site)
            else:
                unreachable.append(site)

    # ── สรุป Terminal ───────────────────────────────────────────────
    print(f"\n{'=' * 75}")
    print(f"  สรุปผลการตรวจสอบ")
    print(f"{'=' * 75}")
    print(f"  ทั้งหมด        : {total} เว็บ")
    print(f"  ✅ เข้าได้      : {len(reachable)} เว็บ ({len(reachable)/total*100:.1f}%)")
    print(f"  ❌ เข้าไม่ได้   : {len(unreachable)} เว็บ ({len(unreachable)/total*100:.1f}%)")

    if unreachable:
        type_counts = Counter(s.get("error_type", "อื่นๆ") for s in unreachable)
        print(f"\n  สาเหตุที่เข้าไม่ได้:")
        for etype, count in type_counts.most_common():
            print(f"    • {etype:45s} : {count:3d} เว็บ")

    # ── Export Excel ────────────────────────────────────────────────
    print(f"\n[*] กำลังบันทึกไฟล์ Excel → {OUTPUT_PATH.name} ...")
    out_wb = openpyxl.Workbook()

    thin_border = Border(
        left=Side(style="thin", color="E0E0E0"),
        right=Side(style="thin", color="E0E0E0"),
        top=Side(style="thin", color="E0E0E0"),
        bottom=Side(style="thin", color="E0E0E0"),
    )

    # ─── Sheet 1: เข้าได้ ────────────────────────────────────────
    ws_good = out_wb.active
    ws_good.title = "เข้าได้ (Reachable)"
    headers_good = ["ลำดับ", "URL", "หมวดหมู่", "HTTP Status", "URL ปลายทาง", "สถานะ / หมายเหตุ", "เวลาตอบ (วินาที)"]
    ws_good.append(headers_good)

    good_fill = PatternFill(start_color="198754", fill_type="solid")
    good_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    for col in range(1, len(headers_good) + 1):
        cell = ws_good.cell(row=1, column=col)
        cell.fill = good_fill
        cell.font = good_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    for i, s in enumerate(sorted(reachable, key=lambda x: x["no"]), 1):
        original = s["url"]
        final = s.get("final_url") or original
        row_data = [
            i,
            original,
            s["category"],
            s.get("status_code", ""),
            final,
            s.get("note", "ปกติ"),
            s.get("duration", 0),
        ]
        ws_good.append(row_data)
        r = ws_good.max_row
        for c in range(1, len(row_data) + 1):
            ws_good.cell(row=r, column=c).border = thin_border
            ws_good.cell(row=r, column=c).font = Font(name="Segoe UI", size=10)

        # URL Hyperlink
        url_cell = ws_good.cell(row=r, column=2)
        url_cell.hyperlink = original if original.startswith("http") else "http://" + original
        url_cell.font = Font(name="Segoe UI", size=10, color="0563C1", underline="single")

        # Destination URL Hyperlink
        final_cell = ws_good.cell(row=r, column=5)
        final_cell.hyperlink = final if final.startswith("http") else "http://" + final
        final_cell.font = Font(name="Segoe UI", size=10, color="0563C1", underline="single")

        # สีสลับแถว
        if i % 2 == 0:
            for c in range(1, len(row_data) + 1):
                ws_good.cell(row=r, column=c).fill = PatternFill(start_color="F4FBF7", fill_type="solid")

    ws_good.column_dimensions["A"].width = 8
    ws_good.column_dimensions["B"].width = 52
    ws_good.column_dimensions["C"].width = 24
    ws_good.column_dimensions["D"].width = 14
    ws_good.column_dimensions["E"].width = 55
    ws_good.column_dimensions["F"].width = 40
    ws_good.column_dimensions["G"].width = 18
    ws_good.auto_filter.ref = ws_good.dimensions

    # ─── Sheet 2: เข้าไม่ได้ ──────────────────────────────────────
    ws_bad = out_wb.create_sheet("เข้าไม่ได้ (Unreachable)")
    headers_bad = ["ลำดับ", "URL", "หมวดหมู่", "HTTP Status", "ประเภทปัญหา", "รายละเอียด Error", "เวลาที่ใช้ (วินาที)"]
    ws_bad.append(headers_bad)

    bad_fill = PatternFill(start_color="DC3545", fill_type="solid")
    bad_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    for col in range(1, len(headers_bad) + 1):
        cell = ws_bad.cell(row=1, column=col)
        cell.fill = bad_fill
        cell.font = bad_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    for i, s in enumerate(sorted(unreachable, key=lambda x: (x.get("error_type", ""), x["no"])), 1):
        row_data = [
            i,
            s["url"],
            s["category"],
            s.get("status_code") or "-",
            s.get("error_type", ""),
            s.get("error", ""),
            s.get("duration", 0),
        ]
        ws_bad.append(row_data)
        r = ws_bad.max_row
        for c in range(1, len(row_data) + 1):
            ws_bad.cell(row=r, column=c).border = thin_border
            ws_bad.cell(row=r, column=c).font = Font(name="Segoe UI", size=10)

        # URL Hyperlink
        url_cell = ws_bad.cell(row=r, column=2)
        link_url = s["url"]
        if not link_url.startswith("http"):
            link_url = "http://" + link_url
        url_cell.hyperlink = link_url
        url_cell.font = Font(name="Segoe UI", size=10, color="0563C1", underline="single")

        # สีสลับแถว
        if i % 2 == 0:
            for c in range(1, len(row_data) + 1):
                ws_bad.cell(row=r, column=c).fill = PatternFill(start_color="FDF4F5", fill_type="solid")

    ws_bad.column_dimensions["A"].width = 8
    ws_bad.column_dimensions["B"].width = 52
    ws_bad.column_dimensions["C"].width = 24
    ws_bad.column_dimensions["D"].width = 14
    ws_bad.column_dimensions["E"].width = 38
    ws_bad.column_dimensions["F"].width = 50
    ws_bad.column_dimensions["G"].width = 18
    ws_bad.auto_filter.ref = ws_bad.dimensions

    # ─── Sheet 3: สรุป ────────────────────────────────────────────
    ws_sum = out_wb.create_sheet("สรุป (Summary)")
    sum_header_fill = PatternFill(start_color="0D6EFD", fill_type="solid")
    sum_header_font = Font(name="Segoe UI", size=12, bold=True, color="FFFFFF")

    ws_sum.append(["รายการ", "จำนวน", "เปอร์เซ็นต์"])
    for col in range(1, 4):
        cell = ws_sum.cell(row=1, column=col)
        cell.fill = sum_header_fill
        cell.font = sum_header_font
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    sum_data = [
        ["ทั้งหมด", total, "100%"],
        ["✅ เข้าได้ (มีหน้าเว็บจริง)", len(reachable), f"{len(reachable)/total*100:.1f}%"],
        ["❌ เข้าไม่ได้ (พัง / จอขาว / ปิด)", len(unreachable), f"{len(unreachable)/total*100:.1f}%"],
    ]
    for row_data in sum_data:
        ws_sum.append(row_data)
        r = ws_sum.max_row
        for c in range(1, 4):
            ws_sum.cell(row=r, column=c).border = thin_border
            ws_sum.cell(row=r, column=c).font = Font(name="Segoe UI", size=11)

    ws_sum.append([])
    ws_sum.append(["สาเหตุที่เข้าไม่ได้", "จำนวน", "เปอร์เซ็นต์"])
    r = ws_sum.max_row
    for c in range(1, 4):
        ws_sum.cell(row=r, column=c).fill = PatternFill(start_color="FFC107", fill_type="solid")
        ws_sum.cell(row=r, column=c).font = Font(name="Segoe UI", size=11, bold=True)
        ws_sum.cell(row=r, column=c).border = thin_border

    if unreachable:
        type_counts = Counter(s.get("error_type", "อื่นๆ") for s in unreachable)
        for etype, count in type_counts.most_common():
            ws_sum.append([etype, count, f"{count/len(unreachable)*100:.1f}%"])
            r = ws_sum.max_row
            for c in range(1, 4):
                ws_sum.cell(row=r, column=c).border = thin_border
                ws_sum.cell(row=r, column=c).font = Font(name="Segoe UI", size=10)

    ws_sum.append([])
    ws_sum.append(["ตรวจล่าสุดเมื่อ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""])

    ws_sum.column_dimensions["A"].width = 45
    ws_sum.column_dimensions["B"].width = 16
    ws_sum.column_dimensions["C"].width = 16

    out_wb.save(OUTPUT_PATH)
    print(f"\n[✅] บันทึกไฟล์เรียบร้อย → {OUTPUT_PATH}")
    print(f"{'=' * 75}")


if __name__ == "__main__":
    main()
