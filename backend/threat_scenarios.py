"""
threat_scenarios.py
Concise, high-impact threat scenarios for NCSA and OWASP security checks.
Attack Vector + Business Impact. Thai language with English technical terms.
"""

from typing import Optional

THREAT_SCENARIOS: dict[str, str] = {
    # ── NCSA / สกมช. (11 security items) ──────────────────────────
    "ncsa-01": "ขาดการบังคับ HTTPS ทำให้ผู้โจมตีทำ Man-in-the-Middle (MitM) ดักจับรหัสผ่านและ Session Token บนเครือข่าย ส่งผลให้ถูกสวมรอยบัญชีและข้อมูลรั่วไหล",
    "ncsa-02": "ขาด HSTS เปิดช่องให้แฮกเกอร์ทำ SSL Stripping บังคับ Downgrade การเชื่อมต่อเป็น HTTP เพื่อดักขโมยข้อมูลสำคัญและ Session Cookie",
    "ncsa-03": "ขาดการป้องกัน Clickjacking ทำให้ผู้โจมตีฝังเว็บลงใน iframe โปร่งใส หลอกให้ผู้ใช้คลิกทำธุรกรรมหรือแก้ไขสิทธิ์โดยไม่รู้ตัว",
    "ncsa-04": "การเปิดเผย Server Version ช่วยให้ผู้โจมตีค้นหา Known Exploit ตรงตาม CVE เพื่อโจมตีช่องโหว่ระดับ OS หรือยึด Server",
    "ncsa-05": "การเปิดใช้ TLS 1.0/1.1 หรือ SSLv3 เสี่ยงต่อการถูกโจมตีแบบ POODLE/BEAST เพื่อถอดรหัสทราฟฟิกและขโมยข้อมูลลับขององค์กร",
    "ncsa-06": "การใช้ Weak Ciphers (เช่น RC4/3DES) เปิดทางให้แฮกเกอร์ถอดรหัสทราฟฟิกเครือข่ายย้อนหลัง ทำให้ข้อมูลสำคัญทางธุรกิจถูกเปิดเผย",
    "ncsa-07": "ช่องโหว่ XSS หรือ SQLi เปิดโอกาสให้แฮกเกอร์รันคำสั่ง Remote Code Execution (RCE), ขโมย Database ทั้งหมด หรือยึดระบบจัดการ",
    "ncsa-08": "คุกกี้ที่ขาด Secure, HttpOnly หรือ SameSite ทำให้แฮกเกอร์ทำ XSS ขโมย Session Cookie หรือทำ CSRF สั่งโอนเงินแทนผู้ใช้",
    "ncsa-09": "การเปิดเผย Framework Version ผ่าน X-Powered-By ทำให้แฮกเกอร์ใช้ Automate Exploit เจาะระบบตามช่องโหว่เฉพาะของเวอร์ชันนั้น",
    "ncsa-10": "ซอฟต์แวร์มีช่องโหว่ CVE สาธารณะที่ยังไม่แพตช์ แฮกเกอร์สามารถใช้ Exploit สำเร็จรูปทำ RCE เพื่อยึดการควบคุม Web Server ได้ทันที",
    "ncsa-11": "หน้า Admin หรือ Login ที่เปิดสู่ Public เสี่ยงต่อการถูก Brute Force หรือ Credential Stuffing จนระบบหลังบ้านถูกยึดครอง",

    # ── OWASP HTTP Security Headers (11 security items) ───────────
    "owasp-01": "เมื่อไม่มี CSP แฮกเกอร์สามารถทำ Stored/Reflected XSS ฝัง JavaScript อันตราย ขโมย Session Token และ Redirect ผู้ใช้ไป Phishing",
    "owasp-02": "ขาด HSTS เสี่ยงต่อ SSL Stripping ทำให้ผู้โจมตีในเครือข่ายเดียวกันดักจับ Plaintext Credentials และข้อมูลธุรกรรมของผู้ใช้",
    "owasp-03": "ขาด X-Frame-Options เปิดทางให้ทำ UI Redressing หรือ Clickjacking หลอกให้เหยื่อกดปุ่มสำคัญ เช่น อนุมัติการจ่ายเงินหรือลบบัญชี",
    "owasp-04": "ขาด X-Content-Type-Options: nosniff ทำให้เบราว์เซอร์เกิด MIME Sniffing รันไฟล์ไม่ปลอดภัยเป็นสคริปต์จนเกิด XSS",
    "owasp-05": "ขาด Referrer-Policy ทำให้ Sensitive Token หรือ Internal URL Parameter ใน Query String รั่วไหลไปยัง External Domains ปลายทาง",
    "owasp-06": "ขาด Permissions-Policy เปิดโอกาสให้ Third-party Scripts หรือ Malvertising แอบเข้าถึง Microphone, Camera หรือ Geolocation ของผู้ใช้",
    "owasp-07": "ขาด Cross-Origin-Opener-Policy (COOP) ทำให้เว็บหน้าอื่นเข้าถึง DOM Context ผ่าน window.opener เสี่ยงต่อ Cross-Origin Information Leakage",
    "owasp-08": "ขาด Cross-Origin-Embedder-Policy (COEP) ทำให้สูญเสีย Cross-Origin Isolation เสี่ยงต่อการถูกโจมตี Side-channel เช่น Spectre ขโมย Data ใน Memory",
    "owasp-09": "ขาด Cross-Origin-Resource-Policy (CORP) เปิดให้เว็บภายนอก Hotlink และดึง Private API Data หรือรูปภาพสำคัญไปใช้งานโดยไม่ได้รับอนุญาต",
    "owasp-10": "ขาด Cache-Control: no-store ทำให้ข้อมูลส่วนบุคคลถูกแคชในเครื่องสาธารณะ ผู้ใช้รายอื่นสามารถกด Back ดึงข้อมูล PII ขึ้นมาดูได้",
    "owasp-11": "Session Cookie ที่ขาด Secure/HttpOnly/SameSite เสี่ยงต่อการถูกขโมยผ่าน XSS/Network Sniffing และถูกโจมตีแบบ CSRF เพื่อเข้ายึด Session",
}


def get_threat_scenario(check_id: str) -> Optional[str]:
    """Return threat scenario for given check_id or None if not applicable."""
    return THREAT_SCENARIOS.get(check_id)
