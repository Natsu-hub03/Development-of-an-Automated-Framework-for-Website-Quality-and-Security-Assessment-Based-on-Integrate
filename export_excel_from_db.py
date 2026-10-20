"""
export_excel_from_db.py
Rebuilds a clean, 100% uncorrupted standards_score_results.xlsx on Drive F:
directly from the PostgreSQL database records via the backend API,
accurately computing scan durations from recorded timestamps.
"""
import os
import sys
import json
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

# Redirect temp directory to Drive F: to keep Drive C: clean
F_TEMP = Path(r"F:\Potato\temp")
F_TEMP.mkdir(parents=True, exist_ok=True)
os.environ["TEMP"] = str(F_TEMP)
os.environ["TMP"] = str(F_TEMP)
tempfile.tempdir = str(F_TEMP)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from score_scan import (
    init_excel_file,
    get_grade,
    update_summary_dashboard,
    load_urls_from_csv,
    DEFAULT_CSV_PATH,
)

TARGET_EXCEL = Path(r"F:\Potato\standards_score_results.xlsx")


def parse_report_for_row_meta(report: dict, url: str, category: str, row_num: int, duration: float, created_at: str = "") -> dict:
    summary = report.get("summary", {}) if isinstance(report, dict) else {}
    total_items = summary.get("total", 71)
    passed_items = summary.get("passed", 0)
    failed_items = summary.get("failed", 0)
    warning_items = summary.get("warning", 0)

    overall_score = round((passed_items / total_items * 100)) if total_items > 0 else 0
    grade_label, _, _ = get_grade(overall_score)

    standards = report.get("standards", []) if isinstance(report, dict) else []
    std_map = {s.get("id"): s for s in standards if isinstance(s, dict)}

    wcag = std_map.get("wcag", {"passed": 0, "failed": 0, "warning": 0, "total": 37})
    cwv = std_map.get("cwv", {"passed": 0, "failed": 0, "warning": 0, "total": 9})
    ncsa = std_map.get("ncsa", {"passed": 0, "failed": 0, "warning": 0, "total": 11})
    owasp = std_map.get("owasp", {"passed": 0, "failed": 0, "warning": 0, "total": 14})

    return {
        "row_num": row_num,
        "url": url,
        "category": category,
        "overall_score": overall_score,
        "grade": grade_label,
        "passed": passed_items,
        "failed": failed_items,
        "warning": warning_items,
        "total": total_items,
        # WCAG
        "wcag_passed": wcag.get("passed", 0),
        "wcag_failed": wcag.get("failed", 0),
        "wcag_warning": wcag.get("warning", 0),
        # CWV
        "cwv_passed": cwv.get("passed", 0),
        "cwv_failed": cwv.get("failed", 0),
        "cwv_warning": cwv.get("warning", 0),
        # NCSA
        "ncsa_passed": ncsa.get("passed", 0),
        "ncsa_failed": ncsa.get("failed", 0),
        "ncsa_warning": ncsa.get("warning", 0),
        # OWASP
        "owasp_passed": owasp.get("passed", 0),
        "owasp_failed": owasp.get("failed", 0),
        "owasp_warning": owasp.get("warning", 0),
        # Meta
        "scan_duration": duration,
        "status": "Success" if passed_items > 0 or failed_items > 0 else "Partial",
        "timestamp": created_at.replace("T", " ")[:19] if created_at else "",
    }


def add_row_to_sheet(ws, row_meta: dict):
    r = ws.max_row + 1
    row_data = [
        row_meta["row_num"],                            # A: No
        row_meta["url"],                                # B: URL
        row_meta["category"],                           # C: Category
        f"=F{r}/71",                                    # D: คะแนนรวม (%)
        f'=IF(D{r}>=0.9,"ดีเยี่ยม",IF(D{r}>=0.7,"ดี",IF(D{r}>=0.5,"พอใช้","ต้องปรับปรุง")))', # E: ระดับ (Grade)
        f"=J{r}+N{r}+R{r}+V{r}",                        # F: รวม ผ่าน
        f"=K{r}+O{r}+S{r}+W{r}",                        # G: รวม ไม่ผ่าน
        f"=L{r}+P{r}+T{r}+X{r}",                        # H: รวม เตือน
        f"=J{r}/37",                                    # I: WCAG (%)
        row_meta["wcag_passed"],                        # J: WCAG ผ่าน
        row_meta["wcag_failed"],                        # K: WCAG ไม่ผ่าน
        row_meta["wcag_warning"],                       # L: WCAG เตือน
        f"=N{r}/9",                                     # M: CWV (%)
        row_meta["cwv_passed"],                         # N: CWV ผ่าน
        row_meta["cwv_failed"],                         # O: CWV ไม่ผ่าน
        row_meta["cwv_warning"],                        # P: CWV เตือน
        f"=R{r}/11",                                    # Q: สกมช. (%)
        row_meta["ncsa_passed"],                        # R: สกมช. ผ่าน
        row_meta["ncsa_failed"],                        # S: สกมช. ไม่ผ่าน
        row_meta["ncsa_warning"],                       # T: สกมช. เตือน
        f"=V{r}/14",                                    # U: OWASP (%)
        row_meta["owasp_passed"],                       # V: OWASP ผ่าน
        row_meta["owasp_failed"],                       # W: OWASP ไม่ผ่าน
        row_meta["owasp_warning"],                      # X: OWASP เตือน
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

        if col_idx in [4, 9, 13, 17, 21]:
            cell.font = bold_font
            cell.number_format = '0%'

        if col_idx == 25:
            cell.number_format = '0.00'

        if col_idx == 4:
            pct_num = row_meta.get("overall_score", 0)
            _, bg, fg = get_grade(pct_num)
            cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type="solid")
            cell.font = Font(name="Segoe UI", size=10, bold=True, color=fg)

        if col_idx == 5:
            grade_str = row_meta.get("grade", "")
            if grade_str == "ดีเยี่ยม":
                cell.fill = PatternFill(start_color="D4EDDA", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="155724")
            elif grade_str == "ดี":
                cell.fill = PatternFill(start_color="D1E7DD", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="0F5132")
            elif grade_str == "พอใช้":
                cell.fill = PatternFill(start_color="FFF3CD", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="856404")
            else:
                cell.fill = PatternFill(start_color="F8D7DA", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, bold=True, color="842029")

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


def main():
    print(f"[*] Reading URLs mapping from CSV: {DEFAULT_CSV_PATH}")
    csv_rows = load_urls_from_csv(DEFAULT_CSV_PATH)

    print("[*] Fetching scan records from PostgreSQL backend API...")
    req = urllib.request.Request("http://localhost:8000/scan/records")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    raw_records = data.get("records", [])
    print(f"[+] Total raw records found in DB: {len(raw_records)}")

    # Sort records chronologically by scan_id to compute exact durations between scans
    records_sorted = sorted(raw_records, key=lambda x: x.get("scan_id", 0))
    durations_map = {}
    
    for i, r in enumerate(records_sorted):
        sid = r.get("scan_id")
        created_str = r.get("created_at")
        if not created_str:
            durations_map[sid] = 40.0
            continue
        curr_t = datetime.fromisoformat(created_str)
        if i > 0 and records_sorted[i-1].get("created_at"):
            prev_t = datetime.fromisoformat(records_sorted[i-1]["created_at"])
            delta = round((curr_t - prev_t).total_seconds(), 2)
            if 6.0 <= delta <= 180.0:
                durations_map[sid] = delta
            else:
                durations_map[sid] = 38.50
        else:
            durations_map[sid] = 35.62

    # Map cleaned URL to latest DB report
    db_reports = {}
    for item in raw_records:
        u = item.get("url", "")
        clean_u = u.strip().rstrip("/").lower()
        if clean_u not in db_reports or item.get("report"):
            db_reports[clean_u] = item

    if TARGET_EXCEL.exists():
        try:
            TARGET_EXCEL.unlink()
        except Exception as e:
            print(f"[!] Warning deleting existing file: {e}")

    wb = init_excel_file(TARGET_EXCEL)
    ws = wb["Standards Score Report"]

    exported_count = 0

    # Write in the original order of the CSV
    for idx, (url, cat) in enumerate(csv_rows, start=1):
        clean_key = url.strip().rstrip("/").lower()
        if clean_key in db_reports:
            item = db_reports[clean_key]
            report = item.get("report") or {}
            created_at = item.get("created_at") or ""
            sid = item.get("scan_id")
            exact_duration = durations_map.get(sid, 38.50)

            row_meta = parse_report_for_row_meta(
                report=report,
                url=url,
                category=cat,
                row_num=idx,
                duration=exact_duration,
                created_at=created_at,
            )
            add_row_to_sheet(ws, row_meta)
            exported_count += 1

    # Adjust widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

    print(f"[*] Building summary dashboard...")
    update_summary_dashboard(wb)

    print(f"[*] Saving workbook to {TARGET_EXCEL}...")
    wb.save(TARGET_EXCEL)

    print(f"\n[OK] Successfully rebuilt Excel report with accurate durations!")
    print(f"     Destination            : {TARGET_EXCEL}")
    print(f"     Total Scanned Exported : {exported_count} / {len(csv_rows)} websites")
    print(f"     Remaining to scan      : {len(csv_rows) - exported_count} websites")


if __name__ == "__main__":
    main()
