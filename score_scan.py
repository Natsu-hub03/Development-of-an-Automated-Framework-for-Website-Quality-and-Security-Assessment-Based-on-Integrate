"""
score_scan.py
Automated Web Standards Assessment & Scoring Script.
Reads URLs from CSV, scans 4 web standards (WCAG 2.1, Core Web Vitals & SEO, สกมช., OWASP),
computes exact compliance scores and grades (matching the system's assessment engine),
and exports real-time results into Excel (.xlsx).
"""
import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add backend directory to sys.path so we can use the evaluation engine directly
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.standards.report_builder import build_standards_report, build_unreachable_standards_report
from services.reachability import check_url

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Error: openpyxl is not installed. Run 'pip install openpyxl'")
    sys.exit(1)


# ── Configuration & Paths ──────────────────────────────────────────────────
import tempfile
F_TEMP = BASE_DIR / "temp"
F_TEMP.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = str(F_TEMP)
os.environ["TMP"] = str(F_TEMP)
os.environ["TMPDIR"] = str(F_TEMP)
tempfile.tempdir = str(F_TEMP)

SCANNER_DIR = BASE_DIR / "scanner"
DEFAULT_CSV_PATH = BASE_DIR / "urls.csv" if (BASE_DIR / "urls.csv").exists() else Path(r"c:\Users\tokyo\OneDrive\Desktop\urls.csv")
DEFAULT_EXCEL_PATH = BASE_DIR / "standards_score_results.xlsx"


def get_grade(pct: int) -> tuple[str, str, str]:
    """
    Returns (label, bg_hex, text_hex)
    Matches the system's evaluation thresholds:
      >= 90 : ดีเยี่ยม (Green)
      >= 70 : ดี (Emerald)
      >= 50 : พอใช้ (Yellow/Orange)
      <  50 : ต้องปรับปรุง (Red)
    """
    if pct >= 90:
        return "ดีเยี่ยม", "D4EDDA", "155724"
    if pct >= 70:
        return "ดี", "D1E7DD", "0F5132"
    if pct >= 50:
        return "พอใช้", "FFF3CD", "856404"
    return "ต้องปรับปรุง", "F8D7DA", "842029"


def run_node_scanner(script_name: str, url: str, timeout: int = 120) -> tuple[dict | None, float, str | None]:
    """Run a Node.js scanner subprocess and return parsed JSON or error."""
    script_path = SCANNER_DIR / script_name
    if not script_path.exists():
        return None, 0.0, f"Script not found: {script_name}"

    start_time = time.perf_counter()
    env = os.environ.copy()
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(chrome_path):
        env["PUPPETEER_EXECUTABLE_PATH"] = chrome_path
        env["CHROME_PATH"] = chrome_path

    try:
        proc = subprocess.run(
            ["node", str(script_path), url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(SCANNER_DIR),
            env=env,
        )
        duration = round(time.perf_counter() - start_time, 2)
        if proc.returncode != 0:
            err = proc.stderr.strip()[:200] or f"Exit code {proc.returncode}"
            return None, duration, err
        try:
            data = json.loads(proc.stdout.strip())
            return data, duration, None
        except Exception:
            return None, duration, "JSON parse error"
    except subprocess.TimeoutExpired:
        duration = round(time.perf_counter() - start_time, 2)
        return None, duration, "Timeout"
    except Exception as e:
        duration = round(time.perf_counter() - start_time, 2)
        return None, duration, str(e)


def scan_via_backend_api(url: str, backend_url: str = "http://localhost:8000", timeout: int = 180) -> tuple[dict | None, float]:
    """Call the backend POST /scan/standards directly (same as Web UI)."""
    import urllib.request
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(
            f"{backend_url}/scan/standards",
            data=json.dumps({"url": url}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = round(time.perf_counter() - t0, 2)
            if data.get("success") and "data" in data:
                return data["data"], elapsed
    except Exception:
        pass
    return None, round(time.perf_counter() - t0, 2)


def evaluate_website_standards(url: str, timeouts: dict[str, int]) -> dict:
    """
    Evaluates website standards directly using Local Standalone scanners.
    Pre-validates reachability: dead/closed sites get 0 across all standards.
    Reachable sites are scanned using their resolved effective URL (HTTP/HTTPS).
    """
    # ── 1. Pre-validation: ตรวจสอบว่าเว็บไซต์เปิดอยู่จริงหรือไม่ ─────────────
    reach = check_url(url)
    if not reach.get("reachable"):
        err_msg = reach.get("error_type") or reach.get("error") or "เว็บไซต์ปิดตัวหรือไม่สามารถเข้าถึงได้"
        print(f"    [!] เว็บไซต์ปิดตัว/เข้าถึงไม่ได้ ({err_msg}) -> กำหนด 0 คะแนนทุกมาตรฐาน")
        return {
            "overall_score": 0,
            "grade": "ต้องปรับปรุง",
            "passed": 0,
            "failed": 71,
            "warning": 0,
            "wcag_score": 0,
            "wcag_passed": 0,
            "wcag_failed": 37,
            "wcag_total": 37,
            "wcag_warning": 0,
            "cwv_score": 0,
            "cwv_passed": 0,
            "cwv_failed": 9,
            "cwv_total": 9,
            "cwv_warning": 0,
            "ncsa_score": 0,
            "ncsa_passed": 0,
            "ncsa_failed": 11,
            "ncsa_total": 11,
            "ncsa_warning": 0,
            "owasp_score": 0,
            "owasp_passed": 0,
            "owasp_failed": 14,
            "owasp_total": 14,
            "owasp_warning": 0,
            "scan_duration": round(reach.get("duration", 0.0), 2),
            "status": f"Dead/Closed ({err_msg})",
            "source_mode": "Reachability Pre-Check",
            "errors": err_msg,
        }

    effective_url = reach.get("final_url") or url
    source_mode = "Local Standalone"
    wall_start = time.perf_counter()
    futures = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures["axe"] = executor.submit(
            run_node_scanner, "axe_scan.js", effective_url, timeouts.get("axe", 90)
        )
        futures["lighthouse"] = executor.submit(
            run_node_scanner, "lighthouse_scan.js", effective_url, timeouts.get("lighthouse", 130)
        )
        futures["headers"] = executor.submit(
            run_node_scanner, "headers_scan.js", effective_url, timeouts.get("headers", 45)
        )
        futures["wappalyzer"] = executor.submit(
            run_node_scanner, "wappalyzer_scan.js", effective_url, timeouts.get("wappalyzer", 100)
        )

        scan_raw = {}
        for key, future in futures.items():
            try:
                data, dur, err = future.result()
                scan_raw[key] = {"data": data, "duration": dur, "error": err}
            except Exception as e:
                scan_raw[key] = {"data": None, "duration": 0.0, "error": str(e)}

    wall_total = round(time.perf_counter() - wall_start, 2)

    # Build standards report using local engine
    report = build_standards_report(
        url=effective_url,
        axe_data=scan_raw["axe"]["data"],
        lighthouse_data=scan_raw["lighthouse"]["data"],
        headers_data=scan_raw["headers"]["data"],
        wappalyzer_data=scan_raw["wappalyzer"]["data"],
        zap_data={},
    )

    summary = report.get("summary", {})
    total_items = summary.get("total", 71)
    passed_items = summary.get("passed", 0)
    failed_items = summary.get("failed", 0)
    warning_items = summary.get("warning", 0)

    overall_score = round((passed_items / total_items * 100)) if total_items > 0 else 0
    grade_label, grade_bg, grade_fg = get_grade(overall_score)

    # Extract individual standards
    std_map = {s["id"]: s for s in report.get("standards", [])}
    wcag = std_map.get("wcag", {"passed": 0, "failed": 0, "warning": 0, "total": 37})
    cwv = std_map.get("cwv", {"passed": 0, "failed": 0, "warning": 0, "total": 9})
    ncsa = std_map.get("ncsa", {"passed": 0, "failed": 0, "warning": 0, "total": 11})
    owasp = std_map.get("owasp", {"passed": 0, "failed": 0, "warning": 0, "total": 14})

    def calc_rate(s):
        tot = s.get("total", 0)
        return round((s.get("passed", 0) / tot * 100)) if tot > 0 else 0

    wcag_score = calc_rate(wcag)
    cwv_score = calc_rate(cwv)
    ncsa_score = calc_rate(ncsa)
    owasp_score = calc_rate(owasp)

    # Check status
    if scan_raw:
        errors = [v["error"] for v in scan_raw.values() if v.get("error")]
        if not errors:
            status = "Success"
        elif len(errors) == len(scan_raw):
            status = "Failed"
        else:
            status = f"Partial ({len(scan_raw) - len(errors)}/{len(scan_raw)})"
    else:
        errors = []
        status = "Success" if report else "Failed"

    return {
        "overall_score": overall_score,
        "grade": grade_label,
        "passed": passed_items,
        "failed": failed_items,
        "warning": warning_items,
        "total": total_items,
        # WCAG 2.1
        "wcag_score": wcag_score,
        "wcag_passed": wcag.get("passed", 0),
        "wcag_failed": wcag.get("failed", 0),
        "wcag_warning": wcag.get("warning", 0),
        "wcag_total": wcag.get("total", 37),
        # CWV & SEO
        "cwv_score": cwv_score,
        "cwv_passed": cwv.get("passed", 0),
        "cwv_failed": cwv.get("failed", 0),
        "cwv_warning": cwv.get("warning", 0),
        "cwv_total": cwv.get("total", 9),
        # NCSA
        "ncsa_score": ncsa_score,
        "ncsa_passed": ncsa.get("passed", 0),
        "ncsa_failed": ncsa.get("failed", 0),
        "ncsa_warning": ncsa.get("warning", 0),
        "ncsa_total": ncsa.get("total", 11),
        # OWASP
        "owasp_score": owasp_score,
        "owasp_passed": owasp.get("passed", 0),
        "owasp_failed": owasp.get("failed", 0),
        "owasp_warning": owasp.get("warning", 0),
        "owasp_total": owasp.get("total", 14),
        # Meta
        "scan_duration": wall_total,
        "status": status,
        "source_mode": source_mode,
        "errors": "; ".join(errors) if errors else "-",
    }


# ── Excel Workbook Formatting ──────────────────────────────────────────────
HEADERS = [
    "No",
    "URL",
    "หมวดหมู่ (Category)",
    "คะแนนรวม (%)",
    "ระดับ (Grade)",
    "ผ่าน (Pass)",
    "ไม่ผ่าน (Fail)",
    "เตือน (Warn)",
    "WCAG 2.1 (%)",
    "WCAG ผ่าน",
    "WCAG ไม่ผ่าน",
    "WCAG เตือน",
    "CWV & SEO (%)",
    "CWV ผ่าน",
    "CWV ไม่ผ่าน",
    "CWV เตือน",
    "สกมช. NCSA (%)",
    "สกมช. ผ่าน",
    "สกมช. ไม่ผ่าน",
    "สกมช. เตือน",
    "OWASP Headers (%)",
    "OWASP ผ่าน",
    "OWASP ไม่ผ่าน",
    "OWASP เตือน",
    "เวลารวม (s)",
    "สถานะ (Status)",
    "Timestamp",
]


def init_excel_file(filepath: Path) -> openpyxl.Workbook:
    """Initialize Excel workbook with styled headers."""
    if filepath.exists():
        try:
            return openpyxl.load_workbook(filepath)
        except Exception:
            pass

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Standards Score Report"

    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="103A5E", end_color="103A5E", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    ws.append(HEADERS)
    ws.row_dimensions[1].height = 30

    for col_idx in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    try:
        wb.save(filepath)
    except PermissionError:
        print(f"\n[!] กรุณาปิดไฟล์ {filepath.name} ในโปรแกรม Excel ก่อนเริ่มรัน!")
        sys.exit(1)
    return wb


def get_existing_scanned_urls(filepath: Path) -> set[str]:
    """Retrieve scanned URLs to allow seamless resume."""
    if not filepath.exists():
        return set()
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb["Standards Score Report"]
        scanned = set()
        for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
            if row and row[1]:
                scanned.add(str(row[1]).strip().rstrip("/").lower())
        wb.close()
        return scanned
    except Exception:
        return set()


def append_score_to_excel(filepath: Path, row_meta: dict):
    """Safely append row with dynamic Excel formulas for percentages and totals."""
    wb = openpyxl.load_workbook(filepath)
    ws = wb["Standards Score Report"]

    r = ws.max_row + 1  # Target row number for formulas

    # Build row data with dynamic Excel formulas
    row_data = [
        row_meta["row_num"],                            # A: No
        row_meta["url"],                                # B: URL
        row_meta["category"],                           # C: Category
        f"=F{r}/71",                                    # D: คะแนนรวม (%)
        f'=IF(F{r}=0,"เว็บปิด",IF(D{r}>=0.9,"ดีมาก",IF(D{r}>=0.7,"ดี",IF(D{r}>=0.5,"พอใช้","ต้องปรับปรุง"))))', # E: ระดับ (Grade)
        f"=J{r}+N{r}+R{r}+V{r}",                        # F: รวม ผ่าน
        f"=K{r}+O{r}+S{r}+W{r}",                        # G: รวม ไม่ผ่าน
        f"=L{r}+P{r}+T{r}+X{r}",                        # H: รวม เตือน
        # WCAG (37 items)
        f"=J{r}/37",                                    # I: WCAG (%)
        row_meta["wcag_passed"],                        # J: WCAG ผ่าน
        row_meta["wcag_failed"],                        # K: WCAG ไม่ผ่าน
        row_meta["wcag_warning"],                       # L: WCAG เตือน
        # CWV (9 items)
        f"=N{r}/9",                                     # M: CWV (%)
        row_meta["cwv_passed"],                         # N: CWV ผ่าน
        row_meta["cwv_failed"],                         # O: CWV ไม่ผ่าน
        row_meta["cwv_warning"],                        # P: CWV เตือน
        # NCSA (11 items)
        f"=R{r}/11",                                    # Q: สกมช. (%)
        row_meta["ncsa_passed"],                        # R: สกมช. ผ่าน
        row_meta["ncsa_failed"],                        # S: สกมช. ไม่ผ่าน
        row_meta["ncsa_warning"],                       # T: สกมช. เตือน
        # OWASP (14 items)
        f"=V{r}/14",                                    # U: OWASP (%)
        row_meta["owasp_passed"],                       # V: OWASP ผ่าน
        row_meta["owasp_failed"],                       # W: OWASP ไม่ผ่าน
        row_meta["owasp_warning"],                      # X: OWASP เตือน
        # Meta
        row_meta["scan_duration"],                      # Y: เวลารวม (s)
        row_meta["status"],                             # Z: สถานะ
        row_meta["timestamp"],                          # AA: Timestamp
    ]

    cell_font = Font(name="Segoe UI", size=10)
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    ws.append(row_data)
    curr_row = ws.max_row
    ws.row_dimensions[curr_row].height = 22

    for col_idx in range(1, len(row_data) + 1):
        cell = ws.cell(row=curr_row, column=col_idx)
        cell.font = cell_font
        cell.border = thin_border

        # Text vs Number Alignment
        if col_idx in [1, 3, 5, 26, 27]:
            cell.alignment = center_align
        elif col_idx == 2:
            cell.alignment = left_align
            url_str = str(cell.value or '').strip()
            if url_str:
                cell.hyperlink = url_str if url_str.startswith('http') else f'http://{url_str}'
                cell.font = Font(name="Segoe UI", size=10, color="0563C1", underline="single")
        else:
            cell.alignment = right_align

        # Format percentages as Excel Percentage format 0%
        if col_idx in [4, 9, 13, 17, 21]:
            cell.font = bold_font
            cell.number_format = '0%'

        # Format scan duration
        if col_idx == 25:
            cell.number_format = '0.00'

        # Highlight Overall Score & Grade
        if col_idx == 4:
            pct_num = row_meta.get("overall_score", 0)
            _, bg, fg = get_grade(pct_num)
            cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
            cell.font = Font(name="Segoe UI", size=10, bold=True, color=fg)

        if col_idx == 5:
            grade_str = row_meta.get("grade", "")
            if grade_str in ["ดีมาก", "ดีเยี่ยม"]:
                cell.fill = PatternFill(start_color="D4EDDA", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="155724")
            elif grade_str == "ดี":
                cell.fill = PatternFill(start_color="CFE2FF", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="084298")
            elif grade_str == "พอใช้":
                cell.fill = PatternFill(start_color="CFF4FC", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="055160")
            elif grade_str == "เว็บปิด":
                cell.fill = PatternFill(start_color="F8D7DA", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="842029")
            else:
                cell.fill = PatternFill(start_color="FFF3CD", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="664D03")

        # Status Badge
        if col_idx == 26:
            val = str(cell.value)
            if "Success" in val:
                cell.fill = PatternFill(start_color="E2EFDA", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, color="276A3C", bold=True)
            elif "Partial" in val:
                cell.fill = PatternFill(start_color="FFF2CC", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, color="8A6D3B", bold=True)
            else:
                cell.fill = PatternFill(start_color="FCE4D6", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, color="C00000", bold=True)

    # Adjust widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    update_summary_dashboard(wb)
    try:
        wb.save(filepath)
    except PermissionError:
        backup_path = filepath.with_name(f"{filepath.stem}_backup_{int(time.time())}.xlsx")
        wb.save(backup_path)
        print(f"\n[!] คำเตือน: ไฟล์ {filepath.name} กำลังเปิดอยู่ใน Excel ทำให้บันทึกทับไม่ได้!")
        print(f"[*] ได้บันทึกข้อมูลสำรองไว้ที่: {backup_path.name} แทนเรียบร้อยแล้ว (ปิด Excel แล้วรันต่อได้ปกติ)")


def update_summary_dashboard(wb: openpyxl.Workbook):
    """Builds a comprehensive Summary Sheet using dynamic Excel formulas."""
    sheet_name = "Summary สถิติภาพรวม"
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]

    ws = wb.create_sheet(title=sheet_name)
    ws_main = wb["Standards Score Report"]

    max_r = ws_main.max_row
    if max_r < 2:
        return

    src = "'Standards Score Report'"

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="103A5E", fill_type="solid")
    title_font = Font(name="Segoe UI", size=13, bold=True, color="0F172A")
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")

    ws.append(["สรุปภาพรวมผลการประเมินมาตรฐานเว็บไซต์ (Assessment Dashboard)", ""])
    ws.cell(row=1, column=1).font = title_font

    # Overview
    ws.append(["จำนวนเว็บไซต์ที่ประเมินแล้ว", f"=COUNTA({src}!B2:B{max_r})"])
    ws.cell(row=2, column=2).number_format = '0" เว็บไซต์"'

    ws.append(["คะแนนเฉลี่ยรวมทุกมาตรฐาน", f"=AVERAGE({src}!D2:D{max_r})"])
    ws.cell(row=3, column=2).number_format = '0.0%'
    ws.cell(row=3, column=2).font = bold_font

    ws.append(["", ""])

    # Section 1: Standards Breakdown
    headers = ["มาตรฐาน (Standard)", "คะแนนเฉลี่ย (%)", "คะแนนต่ำสุด (%)", "คะแนนสูงสุด (%)", "จำนวนรายการ"]
    ws.append(headers)
    hdr_row = ws.max_row
    for c in range(1, 6):
        cell = ws.cell(row=hdr_row, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    std_configs = [
        ("WCAG 2.1 (W3C)", "I", "37 รายการ"),
        ("Core Web Vitals & SEO (Google)", "M", "9 รายการ"),
        ("มาตรฐานความมั่นคงปลอดภัย สกมช.", "Q", "11 รายการ"),
        ("OWASP HTTP Security Headers", "U", "14 รายการ"),
        ("คะแนนเฉลี่ยรวม (Overall Score)", "D", "71 รายการ"),
    ]

    for name, col, count_label in std_configs:
        ws.append([
            name,
            f"=AVERAGE({src}!{col}2:{col}{max_r})",
            f"=MIN({src}!{col}2:{col}{max_r})",
            f"=MAX({src}!{col}2:{col}{max_r})",
            count_label
        ])
        curr = ws.max_row
        ws.cell(row=curr, column=1).font = bold_font
        for c in range(2, 5):
            cell = ws.cell(row=curr, column=c)
            cell.number_format = '0.0%'
            cell.alignment = right_align
        ws.cell(row=curr, column=5).alignment = center_align

    ws.append(["", ""])

    # Section 2: Grade Distribution
    ws.append(["การกระจายตัวของระดับผลการประเมิน (Grade Distribution)", ""])
    ws.cell(row=ws.max_row, column=1).font = Font(name="Segoe UI", size=11, bold=True)
    ws.append(["ระดับ (Grade)", "เกณฑ์คะแนน", "จำนวนเว็บ", "คิดเป็นเปอร์เซ็นต์"])
    g_hdr = ws.max_row
    for c in range(1, 5):
        cell = ws.cell(row=g_hdr, column=c)
        cell.font = header_font
        cell.fill = PatternFill(start_color="334155", fill_type="solid")
        cell.alignment = center_align

    grades_info = [
        ("ดีเยี่ยม", "≥ 90%"),
        ("ดี", "70% – 89%"),
        ("พอใช้", "50% – 69%"),
        ("ต้องปรับปรุง", "< 50%"),
    ]
    for lbl, crit in grades_info:
        r_num = ws.max_row + 1
        ws.append([
            lbl,
            crit,
            f'=COUNTIF({src}!E2:E{max_r}, "{lbl}")',
            f'=C{r_num}/B2'
        ])
        ws.cell(row=r_num, column=3).number_format = '0" เว็บ"'
        ws.cell(row=r_num, column=3).alignment = right_align
        ws.cell(row=r_num, column=4).number_format = '0.0%'
        ws.cell(row=r_num, column=4).alignment = right_align

    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 18)


# ── CSV Reader ───────────────────────────────────────────────────────────────
def load_urls_from_csv(csv_path: Path) -> list[tuple[str, str]]:
    """Load URLs and categories from CSV, with automatic fallback to Excel if CSV not found."""
    if not csv_path.exists():
        local_csv = BASE_DIR / "urls.csv"
        if local_csv.exists():
            csv_path = local_csv
        elif DEFAULT_EXCEL_PATH.exists():
            print(f"[*] Notice: CSV not found at '{csv_path}', loading URLs from '{DEFAULT_EXCEL_PATH.name}' instead...")
            items = []
            wb = openpyxl.load_workbook(DEFAULT_EXCEL_PATH, data_only=True)
            ws = wb.active
            for r in range(2, ws.max_row + 1):
                url = ws.cell(row=r, column=2).value
                cat = ws.cell(row=r, column=3).value or "-"
                if url and (str(url).startswith("http://") or str(url).startswith("https://")):
                    items.append((str(url).strip(), str(cat).strip()))
            return items
        else:
            raise FileNotFoundError(f"Neither CSV nor Excel found: {csv_path}")

    items = []
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",", 1)
            url = parts[0].strip()
            cat = parts[1].strip() if len(parts) > 1 else "-"
            if url.startswith("http://") or url.startswith("https://"):
                items.append((url, cat))
    return items


# ── Main Entrypoint ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Auto Web Standards Scoring to Excel")
    parser.add_argument("--csv", type=str, default=str(DEFAULT_CSV_PATH), help="Path to urls.csv")
    parser.add_argument("--excel", type=str, default=str(DEFAULT_EXCEL_PATH), help="Output Excel path")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of URLs to scan (0 = all)")
    parser.add_argument("--start", type=int, default=1, help="Start from row index (1-based)")
    parser.add_argument("--timeout", type=int, default=90, help="Default scanner timeout in seconds")
    parser.add_argument("--fresh", action="store_true", help="Start a clean fresh scan from scratch (backs up existing Excel)")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    excel_path = Path(args.excel)

    print("=" * 68)
    print("  Auto Web Standards Assessment & Scoring (Excel Export)")
    print("  Standards: WCAG 2.1 | CWV & SEO | สกมช. (NCSA) | OWASP Headers")
    print("=" * 68)
    print(f"[*] Reading URLs from : {csv_path}")
    print(f"[*] Exporting to Excel : {excel_path}")

    urls_with_cat = load_urls_from_csv(csv_path)
    total_in_csv = len(urls_with_cat)
    print(f"[*] Total URLs found  : {total_in_csv}")

    if args.fresh and excel_path.exists():
        backup_name = f"standards_score_results_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        backup_path = excel_path.parent / backup_name
        try:
            import shutil
            shutil.copy2(excel_path, backup_path)
            excel_path.unlink()
            print(f"[*] Fresh mode: สำรองไฟล์เดิมไว้ที่ -> {backup_name}")
        except Exception as e:
            print(f"[!] Warning on backup/unlink: {e}")

    init_excel_file(excel_path)
    scanned_urls = get_existing_scanned_urls(excel_path) if not args.fresh else set()
    print(f"[*] Already scanned   : {len(scanned_urls)} URLs (will resume automatically)")

    start_idx = max(1, args.start) - 1
    items_to_process = urls_with_cat[start_idx:]
    if args.limit > 0:
        items_to_process = items_to_process[:args.limit]

    print(f"[*] URLs to process   : {len(items_to_process)}")
    print("-" * 68)

    timeouts = {
        "axe": args.timeout,
        "lighthouse": min(args.timeout + 30, 150),
        "headers": min(args.timeout, 45),
        "wappalyzer": args.timeout,
    }

    count = 0
    for idx, (url, category) in enumerate(items_to_process, start=1):
        clean_u = url.strip().rstrip("/").lower()
        if clean_u in scanned_urls:
            print(f"[{idx}/{len(items_to_process)}] Skipping (already scanned): {url}")
            continue

        print(f"\n[{idx}/{len(items_to_process)}] Assessing: {url} ({category}) ...")
        try:
            res = evaluate_website_standards(url, timeouts)
        except Exception as e:
            print(f"    [!] เว็บไซต์เข้าถึงไม่ได้ / ขัดข้อง: {e}")
            res = {
                "overall_score": 0,
                "grade": "ต้องปรับปรุง",
                "passed": 0,
                "failed": 71,
                "warning": 0,
                "wcag_score": 0,
                "wcag_passed": 0,
                "wcag_failed": 37,
                "wcag_warning": 0,
                "cwv_score": 0,
                "cwv_passed": 0,
                "cwv_failed": 9,
                "cwv_warning": 0,
                "ncsa_score": 0,
                "ncsa_passed": 0,
                "ncsa_failed": 11,
                "ncsa_warning": 0,
                "owasp_score": 0,
                "owasp_passed": 0,
                "owasp_failed": 14,
                "owasp_warning": 0,
                "scan_duration": 0.0,
                "status": f"Failed ({type(e).__name__})",
                "source_mode": "-",
                "errors": str(e),
            }

        row_num = len(scanned_urls) + 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row_meta = {
            "row_num": row_num,
            "url": url,
            "category": category,
            "overall_score": res["overall_score"],
            "grade": res["grade"],
            "passed": res["passed"],
            "failed": res["failed"],
            "warning": res["warning"],
            "wcag_passed": res["wcag_passed"],
            "wcag_failed": res["wcag_failed"],
            "wcag_warning": res["wcag_warning"],
            "cwv_passed": res["cwv_passed"],
            "cwv_failed": res["cwv_failed"],
            "cwv_warning": res["cwv_warning"],
            "ncsa_passed": res["ncsa_passed"],
            "ncsa_failed": res["ncsa_failed"],
            "ncsa_warning": res["ncsa_warning"],
            "owasp_passed": res["owasp_passed"],
            "owasp_failed": res["owasp_failed"],
            "owasp_warning": res["owasp_warning"],
            "scan_duration": res["scan_duration"],
            "status": res["status"],
            "timestamp": timestamp,
        }

        append_score_to_excel(excel_path, row_meta)
        scanned_urls.add(clean_u)
        count += 1

        print(f"    ├─ คะแนนรวมตามมาตรฐาน : {res['overall_score']}% ({res['grade']}) | ผ่าน: {res['passed']}/71 ตก: {res['failed']} เตือน: {res['warning']}")
        print(f"    ├─ WCAG 2.1            : {res['wcag_score']}% ({res['wcag_passed']}/{res['wcag_total']} ผ่าน, {res['wcag_failed']} ตก)")
        print(f"    ├─ CWV & SEO           : {res['cwv_score']}% ({res['cwv_passed']}/{res['cwv_total']} ผ่าน, {res['cwv_failed']} ตก)")
        print(f"    ├─ สกมช. NCSA          : {res['ncsa_score']}% ({res['ncsa_passed']}/{res['ncsa_total']} ผ่าน, {res['ncsa_failed']} ตก)")
        print(f"    ├─ OWASP Headers       : {res['owasp_score']}% ({res['owasp_passed']}/{res['owasp_total']} ผ่าน, {res['owasp_failed']} ตก)")
        print(f"    ├─ โหมดการสแกน        : {res['source_mode']}")
        print(f"    ├─ เวลาที่ใช้          : {res['scan_duration']}s")
        print(f"    └─ Saved to Excel checkpoint!")

    print("\n" + "=" * 68)
    print(f"Completed! Total new sites assessed: {count}")
    print(f"Excel file saved at: {excel_path}")
    print("=" * 68)


if __name__ == "__main__":
    main()
