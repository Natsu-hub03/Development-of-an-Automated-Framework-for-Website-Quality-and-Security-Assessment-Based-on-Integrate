"""
repair_scan.py
Targeted Repair & Re-assessment Script for standards_score_results.xlsx.
- Re-evaluates websites that had incomplete/missing scans (e.g. WCAG 0/0).
- Re-evaluates dead/closed websites to ensure they strictly receive 0 score across all standards.
- Updates standards_score_results.xlsx in-place while preserving hyperlinks and formatting.
"""
import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import openpyxl
from openpyxl.styles import Font

from score_scan import evaluate_website_standards, get_grade

EXCEL_PATH = BASE_DIR / "standards_score_results.xlsx"


def identify_rows_to_repair(ws) -> list[tuple[int, str, str, str]]:
    """
    Finds rows that need repair:
    1. wcag_passed == 0 and wcag_failed == 0 (Axe failed / missing WCAG score)
    2. Status contains 'Partial'
    3. Site was dead but got score > 0 (e.g., failed CWV & WCAG but got NCSA)
    """
    rows_to_repair = []
    for r in range(2, ws.max_row + 1):
        url = str(ws.cell(r, 2).value or "").strip()
        cat = str(ws.cell(r, 3).value or "").strip()
        wcag_pass = ws.cell(r, 10).value
        wcag_fail = ws.cell(r, 11).value
        cwv_pass = ws.cell(r, 14).value
        status = str(ws.cell(r, 26).value or "").strip()

        needs_repair = False
        reason = ""

        # Check 1: Missing WCAG evaluation
        if wcag_pass == 0 and (wcag_fail == 0 or wcag_fail is None):
            needs_repair = True
            reason = "WCAG 0/0 (Missing Axe scan)"
        elif "Partial" in status:
            needs_repair = True
            reason = f"Status {status}"
        # Check 2: WCAG=0 and CWV=0 but total passed > 0 (Dead site that leaked NCSA points)
        elif wcag_pass == 0 and cwv_pass == 0 and status != "Success":
            total_pass = (ws.cell(r, 10).value or 0) + (ws.cell(r, 14).value or 0) + (ws.cell(r, 18).value or 0) + (ws.cell(r, 22).value or 0)
            if total_pass > 0:
                needs_repair = True
                reason = f"Dead site leaking points ({total_pass} passed)"

        if needs_repair and url:
            rows_to_repair.append((r, url, cat, reason))

    return rows_to_repair


def update_excel_row(ws, r: int, res: dict, url: str, cat: str):
    """Updates an existing row in worksheet with re-evaluated results."""
    # Row formulas & values
    # Col A (1): No (keep existing)
    # Col B (2): URL (preserve hyperlink)
    cell_b = ws.cell(r, 2)
    cell_b.value = url
    cell_b.hyperlink = url if url.startswith("http") else f"http://{url}"
    cell_b.font = Font(name="Segoe UI", size=10, color="0563C1", underline="single")

    # Col C (3): Category
    ws.cell(r, 3).value = cat

    # Formulas
    ws.cell(r, 4).value = f"=F{r}/71"
    ws.cell(r, 5).value = f'=IF(D{r}>=0.9,"ดีเยี่ยม",IF(D{r}>=0.7,"ดี",IF(D{r}>=0.5,"พอใช้","ต้องปรับปรุง")))'
    ws.cell(r, 6).value = f"=J{r}+N{r}+R{r}+V{r}"
    ws.cell(r, 7).value = f"=K{r}+O{r}+S{r}+W{r}"
    ws.cell(r, 8).value = f"=L{r}+P{r}+T{r}+X{r}"

    # WCAG
    ws.cell(r, 9).value = f"=J{r}/37"
    ws.cell(r, 10).value = res["wcag_passed"]
    ws.cell(r, 11).value = res["wcag_failed"]
    ws.cell(r, 12).value = res["wcag_warning"]

    # CWV
    ws.cell(r, 13).value = f"=N{r}/9"
    ws.cell(r, 14).value = res["cwv_passed"]
    ws.cell(r, 15).value = res["cwv_failed"]
    ws.cell(r, 16).value = res["cwv_warning"]

    # NCSA
    ws.cell(r, 17).value = f"=R{r}/11"
    ws.cell(r, 18).value = res["ncsa_passed"]
    ws.cell(r, 19).value = res["ncsa_failed"]
    ws.cell(r, 20).value = res["ncsa_warning"]

    # OWASP
    ws.cell(r, 21).value = f"=V{r}/14"
    ws.cell(r, 22).value = res["owasp_passed"]
    ws.cell(r, 23).value = res["owasp_failed"]
    ws.cell(r, 24).value = res["owasp_warning"]

    # Meta
    ws.cell(r, 25).value = res["scan_duration"]
    ws.cell(r, 26).value = res["status"]
    ws.cell(r, 27).value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    print("=" * 68)
    print("  Targeted Scan Repair (WCAG Protocol Fallback & Dead Sites 0-Score)")
    print("=" * 68)

    if not EXCEL_PATH.exists():
        print(f"[!] Excel file not found: {EXCEL_PATH}")
        sys.exit(1)

    backup_name = f"standards_score_results_backup_before_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    backup_path = BASE_DIR / backup_name
    shutil.copy2(EXCEL_PATH, backup_path)
    print(f"[*] สำรองไฟล์เดิมไว้ที่ -> {backup_name}")

    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["Standards Score Report"]

    rows_to_repair = identify_rows_to_repair(ws)
    print(f"[*] พบแถวที่ต้องปรับปรุง/ตรวจซ่อม: {len(rows_to_repair)} เว็บไซต์")
    print("-" * 68)

    timeouts = {
        "axe": 90,
        "lighthouse": 130,
        "headers": 45,
        "wappalyzer": 100,
    }

    repaired_count = 0
    for idx, (r, url, cat, reason) in enumerate(rows_to_repair, start=1):
        print(f"\n[{idx}/{len(rows_to_repair)}] Re-assessing Row {r}: {url} ({cat})")
        print(f"    └─ สาเหตุที่ตรวจซ่อม: {reason}")

        try:
            res = evaluate_website_standards(url, timeouts)
        except Exception as e:
            print(f"    [!] Error during evaluation: {e}")
            res = {
                "overall_score": 0,
                "grade": "ต้องปรับปรุง",
                "passed": 0,
                "failed": 71,
                "warning": 0,
                "wcag_passed": 0,
                "wcag_failed": 37,
                "wcag_total": 37,
                "wcag_warning": 0,
                "cwv_passed": 0,
                "cwv_failed": 9,
                "cwv_total": 9,
                "cwv_warning": 0,
                "ncsa_passed": 0,
                "ncsa_failed": 11,
                "ncsa_total": 11,
                "ncsa_warning": 0,
                "owasp_passed": 0,
                "owasp_failed": 14,
                "owasp_total": 14,
                "owasp_warning": 0,
                "scan_duration": 0.0,
                "status": f"Dead/Closed (Error: {type(e).__name__})",
            }

        update_excel_row(ws, r, res, url, cat)
        repaired_count += 1

        print(f"    ├─ ผลลัพธ์ใหม่       : คะแนน {res['overall_score']}% ({res['grade']}) | ผ่าน: {res['passed']}/71 ตก: {res['failed']}")
        print(f"    ├─ WCAG 2.1         : ผ่าน {res['wcag_passed']}/37, ตก {res['wcag_failed']}")
        print(f"    ├─ CWV & SEO        : ผ่าน {res['cwv_passed']}/9, ตก {res['cwv_failed']}")
        print(f"    ├─ สกมช. NCSA       : ผ่าน {res['ncsa_passed']}/11, ตก {res['ncsa_failed']}")
        print(f"    ├─ OWASP Headers    : ผ่าน {res['owasp_passed']}/14, ตก {res['owasp_failed']}")
        print(f"    ├─ สถานะ            : {res['status']}")
        print(f"    └─ Saved row {r} to Excel checkpoint!")

        # Checkpoint save every 5 rows and at the end
        if repaired_count % 5 == 0 or repaired_count == len(rows_to_repair):
            wb.save(EXCEL_PATH)

    wb.save(EXCEL_PATH)
    print("\n" + "=" * 68)
    print(f"Repair Complete! Total repaired websites: {repaired_count}")
    print(f"Excel file updated at: {EXCEL_PATH}")
    print("=" * 68)


if __name__ == "__main__":
    main()
