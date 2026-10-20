"""
benchmark_scan.py
Automated web scan benchmark script.
Reads URLs from CSV, measures scan duration per standard (WCAG, CWV, NCSA, OWASP),
records total scan time, and saves real-time results into Excel (.xlsx).
"""
import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Error: openpyxl is not installed. Run 'pip install openpyxl'")
    sys.exit(1)


# ── Configuration & Paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
SCANNER_DIR = BASE_DIR / "scanner"

DEFAULT_CSV_PATH = Path(r"c:\Users\tokyo\OneDrive\Desktop\urls.csv")
DEFAULT_EXCEL_PATH = Path(r"c:\Users\tokyo\OneDrive\Desktop\scan_benchmark_results.xlsx")


def run_node_scanner(script_name: str, url: str, timeout: int = 120) -> tuple[dict | None, float, str | None]:
    """
    Run a Node.js scanner script and measure elapsed execution time.
    Returns: (result_dict, duration_seconds, error_message)
    """
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


def scan_website_standards(url: str, timeouts: dict[str, int]) -> dict:
    """
    Runs all tools concurrently (similar to backend production mode)
    and measures durations per standard:
      - WCAG: axe_scan.js
      - CWV: lighthouse_scan.js
      - NCSA: max(headers_scan.js, wappalyzer_scan.js)
      - OWASP: headers_scan.js
      - Total: Total wall-clock time
    """
    wall_start = time.perf_counter()
    futures = {}
    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures["axe"] = executor.submit(
            run_node_scanner, "axe_scan.js", url, timeouts.get("axe", 90)
        )
        futures["lighthouse"] = executor.submit(
            run_node_scanner, "lighthouse_scan.js", url, timeouts.get("lighthouse", 120)
        )
        futures["headers"] = executor.submit(
            run_node_scanner, "headers_scan.js", url, timeouts.get("headers", 60)
        )
        futures["wappalyzer"] = executor.submit(
            run_node_scanner, "wappalyzer_scan.js", url, timeouts.get("wappalyzer", 120)
        )

        for key, future in futures.items():
            try:
                data, dur, err = future.result()
                results[key] = {"data": data, "duration": dur, "error": err}
            except Exception as e:
                results[key] = {"data": None, "duration": 0.0, "error": str(e)}

    wall_total = round(time.perf_counter() - wall_start, 2)

    # Durations per standard
    wcag_time = results["axe"]["duration"]
    cwv_time = results["lighthouse"]["duration"]
    headers_time = results["headers"]["duration"]
    wap_time = results["wappalyzer"]["duration"]

    # NCSA uses both headers and wappalyzer (in parallel, effective time is max)
    ncsa_time = max(headers_time, wap_time)
    owasp_time = headers_time

    # Determine status
    errors = [v["error"] for v in results.values() if v["error"]]
    if not errors:
        status = "Success"
    elif len(errors) == len(results):
        status = "Failed"
    else:
        status = f"Partial ({len(results) - len(errors)}/{len(results)})"

    return {
        "wcag_time": wcag_time,
        "cwv_time": cwv_time,
        "ncsa_time": ncsa_time,
        "owasp_time": owasp_time,
        "total_time": wall_total,
        "status": status,
        "errors": "; ".join(errors) if errors else "-",
    }


# ── Excel Workbook Manager ──────────────────────────────────────────────────
HEADERS = [
    "No",
    "URL",
    "หมวดหมู่ (Category)",
    "WCAG 2.1 (s)",
    "Core Web Vitals & SEO (s)",
    "สกมช. NCSA (s)",
    "OWASP Headers (s)",
    "Total Time (s)",
    "Status",
    "Timestamp",
    "Error Details",
]


def init_excel_file(filepath: Path) -> openpyxl.Workbook:
    """Initialize or load Excel workbook with beautiful header styling."""
    if filepath.exists():
        try:
            return openpyxl.load_workbook(filepath)
        except Exception:
            pass

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Scan Benchmark"

    # Header styling
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    ws.append(HEADERS)
    ws.row_dimensions[1].height = 28

    for col_idx in range(1, len(HEADERS) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    wb.save(filepath)
    return wb


def get_existing_scanned_urls(filepath: Path) -> set[str]:
    """Read existing scanned URLs from Excel to enable resume capability."""
    if not filepath.exists():
        return set()
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb["Scan Benchmark"]
        scanned = set()
        for row in ws.iter_rows(min_row=2, max_col=2, values_only=True):
            if row and row[1]:
                scanned.add(str(row[1]).strip().lower())
        wb.close()
        return scanned
    except Exception:
        return set()


def append_result_to_excel(filepath: Path, row_data: list):
    """Safely append row to Excel and save immediately."""
    wb = openpyxl.load_workbook(filepath)
    ws = wb["Scan Benchmark"]

    cell_font = Font(name="Segoe UI", size=10)
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="E0E0E0"),
        right=Side(style="thin", color="E0E0E0"),
        top=Side(style="thin", color="E0E0E0"),
        bottom=Side(style="thin", color="E0E0E0"),
    )

    ws.append(row_data)
    curr_row = ws.max_row
    ws.row_dimensions[curr_row].height = 20

    # Alignments: 1: center, 2: left, 3: center, 4-8: right (numbers), 9-10: center, 11: left
    for col_idx in range(1, len(row_data) + 1):
        cell = ws.cell(row=curr_row, column=col_idx)
        cell.font = cell_font
        cell.border = thin_border
        if col_idx in [1, 3, 9, 10]:
            cell.alignment = center_align
        elif col_idx in [4, 5, 6, 7, 8]:
            cell.alignment = right_align
            if isinstance(cell.value, (int, float)):
                cell.number_format = "0.00"
        else:
            cell.alignment = left_align

        # Highlight Status
        if col_idx == 9:
            val = str(cell.value)
            if "Success" in val:
                cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, color="276A3C", bold=True)
            elif "Partial" in val:
                cell.fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, color="8A6D3B", bold=True)
            else:
                cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
                cell.font = Font(name="Segoe UI", size=10, color="C00000", bold=True)

    # Auto-adjust column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Update or create Summary Sheet
    update_summary_sheet(wb)

    wb.save(filepath)


def update_summary_sheet(wb: openpyxl.Workbook):
    """Create or refresh statistics summary sheet."""
    sheet_name = "Summary สถิติ"
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]

    ws_sum = wb.create_sheet(title=sheet_name)
    ws_main = wb["Scan Benchmark"]

    total_scanned = ws_main.max_row - 1
    if total_scanned <= 0:
        return

    wcag_times = []
    cwv_times = []
    ncsa_times = []
    owasp_times = []
    total_times = []
    success_count = 0

    for row in ws_main.iter_rows(min_row=2, max_col=9, values_only=True):
        if not row or not row[1]:
            continue
        try:
            if isinstance(row[3], (int, float)): wcag_times.append(row[3])
            if isinstance(row[4], (int, float)): cwv_times.append(row[4])
            if isinstance(row[5], (int, float)): ncsa_times.append(row[5])
            if isinstance(row[6], (int, float)): owasp_times.append(row[6])
            if isinstance(row[7], (int, float)): total_times.append(row[7])
            if row[8] and "Success" in str(row[8]): success_count += 1
        except Exception:
            pass

    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    normal_font = Font(name="Segoe UI", size=10)

    ws_sum.append(["สรุปภาพรวมการสแกน (Benchmark Summary)", ""])
    ws_sum.append(["จำนวนเว็บไซต์ที่สแกนสำเร็จ", f"{total_scanned} เว็บ"])
    ws_sum.append(["อัตราสำเร็จสมบูรณ์ (Success Rate)", f"{(success_count/total_scanned*100):.1f}%" if total_scanned else "0%"])
    ws_sum.append(["", ""])

    headers = ["มาตรฐาน (Standard)", "เวลาเฉลี่ย (Avg s)", "เร็วสุด (Min s)", "ช้าสุด (Max s)"]
    ws_sum.append(headers)
    hdr_row = ws_sum.max_row
    for col_idx in range(1, len(headers) + 1):
        c = ws_sum.cell(row=hdr_row, column=col_idx)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center")

    def stats(arr):
        if not arr: return (0, 0, 0)
        return (round(sum(arr)/len(arr), 2), round(min(arr), 2), round(max(arr), 2))

    rows = [
        ("WCAG 2.1 (Axe-core)", *stats(wcag_times)),
        ("Core Web Vitals & SEO (Lighthouse)", *stats(cwv_times)),
        ("สกมช. NCSA (Headers + Wappalyzer)", *stats(ncsa_times)),
        ("OWASP Headers", *stats(owasp_times)),
        ("เวลารวมทั้งหมดต่อเว็บ (Total Time)", *stats(total_times)),
    ]

    for r in rows:
        ws_sum.append(list(r))
        ws_sum.cell(row=ws_sum.max_row, column=1).font = bold_font
        for c_idx in range(2, 5):
            cell = ws_sum.cell(row=ws_sum.max_row, column=c_idx)
            cell.font = normal_font
            cell.number_format = "0.00"

    for col in ws_sum.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(c.value or '')) for c in col)
        ws_sum.column_dimensions[col_letter].width = max(max_len + 4, 18)


# ── CSV Reader ───────────────────────────────────────────────────────────────
def load_urls_from_csv(csv_path: Path) -> list[tuple[str, str]]:
    """Load URLs and categories from CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

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
    parser = argparse.ArgumentParser(description="Auto Web Scan Benchmark to Excel")
    parser.add_argument("--csv", type=str, default=str(DEFAULT_CSV_PATH), help="Path to urls.csv")
    parser.add_argument("--excel", type=str, default=str(DEFAULT_EXCEL_PATH), help="Output Excel path")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of URLs to scan (0 = all)")
    parser.add_argument("--start", type=int, default=1, help="Start from row index (1-based)")
    parser.add_argument("--timeout", type=int, default=90, help="Default scanner timeout in seconds")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    excel_path = Path(args.excel)

    print("=" * 65)
    print("  Auto Web Standards Scan Benchmark (Excel Export)")
    print("=" * 65)
    print(f"[*] Reading URLs from : {csv_path}")
    print(f"[*] Exporting to Excel : {excel_path}")

    urls_with_cat = load_urls_from_csv(csv_path)
    total_in_csv = len(urls_with_cat)
    print(f"[*] Total URLs found  : {total_in_csv}")

    init_excel_file(excel_path)
    scanned_urls = get_existing_scanned_urls(excel_path)
    print(f"[*] Already scanned   : {len(scanned_urls)} URLs (will resume automatically)")

    start_idx = max(1, args.start) - 1
    items_to_process = urls_with_cat[start_idx:]
    if args.limit > 0:
        items_to_process = items_to_process[:args.limit]

    print(f"[*] URLs to process   : {len(items_to_process)}")
    print("-" * 65)

    timeouts = {
        "axe": args.timeout,
        "lighthouse": min(args.timeout + 30, 150),
        "headers": min(args.timeout, 45),
        "wappalyzer": args.timeout,
    }

    count = 0
    for idx, (url, category) in enumerate(items_to_process, start=1):
        if url.strip().lower() in scanned_urls:
            print(f"[{idx}/{len(items_to_process)}] Skipping (already scanned): {url}")
            continue

        count += 1
        print(f"\n[{idx}/{len(items_to_process)}] Scanning: {url} ({category})")
        
        result = scan_website_standards(url, timeouts)

        row_num = len(get_existing_scanned_urls(excel_path)) + 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            row_num,
            url,
            category,
            result["wcag_time"],
            result["cwv_time"],
            result["ncsa_time"],
            result["owasp_time"],
            result["total_time"],
            result["status"],
            timestamp,
            result["errors"],
        ]

        append_result_to_excel(excel_path, row)
        scanned_urls.add(url.strip().lower())

        print(f"    ├─ WCAG 2.1 : {result['wcag_time']:>6.2f}s")
        print(f"    ├─ CWV/SEO  : {result['cwv_time']:>6.2f}s")
        print(f"    ├─ NCSA     : {result['ncsa_time']:>6.2f}s")
        print(f"    ├─ OWASP    : {result['owasp_time']:>6.2f}s")
        print(f"    ├─ TOTAL    : {result['total_time']:>6.2f}s | Status: {result['status']}")
        print(f"    └─ Saved to Excel checkpoint!")

    print("\n" + "=" * 65)
    print(f"Completed! Total new sites scanned: {count}")
    print(f"Excel file saved at: {excel_path}")
    print("=" * 65)


if __name__ == "__main__":
    main()
