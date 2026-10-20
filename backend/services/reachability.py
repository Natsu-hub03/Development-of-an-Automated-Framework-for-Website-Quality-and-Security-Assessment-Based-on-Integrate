"""
backend/services/reachability.py
ตรวจสอบความพร้อมในการเข้าถึงเว็บไซต์ (Website Reachability & Availability Service)
รองรับ:
- HTTPS-First: ลองเชื่อมต่อผ่าน HTTPS ก่อนเสมอ
- Automatic Redirect: วิ่งตาม Meta Refresh, Header Refresh และ JavaScript window.location
- Cloudflare WAF: แยกแยะ 403 ของ Cloudflare Bot Challenge ออกจาก 403 ที่เซิร์ฟเวอร์ตายจริง
- DNS Fallback: หาก ISP บล็อก DNS จะใช้ Google DNS (DoH) ตรวจสอบความมีอยู่จริงของโดเมน
- Content Validation: คัดกรองหน้าจอขาว, Fatal Error, PHP Warning, Database Crash, โดเมนหมดอายุ
"""
import time
import ssl
import json
import socket
import re
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional

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


def try_request(url: str, timeout: int = TIMEOUT) -> dict:
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
                if "11001" in reason or "getaddrinfo failed" in reason.lower() or "not known" in reason.lower():
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
    elif "getaddrinfo failed" in err_lower or "name or service not known" in err_lower or "nodename nor servname" in err_lower or "11001" in err_lower:
        error_type = "DNS Error (หาเว็บไม่เจอ)"
    elif "10061" in err_lower or "connection refused" in err_lower:
        error_type = "Connection Refused (Server ปิด)"
    elif "10054" in err_lower or "connection reset" in err_lower or "reset by peer" in err_lower:
        error_type = "Connection Reset (Server ตัดสาย)"
    elif "ssl" in err_lower or "certificate" in err_lower:
        error_type = "SSL/TLS Error"
    else:
        error_type = "การเชื่อมต่อล้มเหลว (เว็บไซต์ถูกปิดหรือไม่สามารถเข้าถึงได้)"

    return {
        "reachable": False,
        "status_code": last_status,
        "final_url": None,
        "note": None,
        "error_type": error_type,
        "error": last_error,
        "duration": elapsed,
    }
