"""
apply_custom_colors.py
Applies user's custom color scheme and updated Grade formula to standards_score_results.xlsx:
- ดีมาก (>=90%): สีเขียว (Green)
- ดี (70%-89%): สีน้ำเงิน (Blue)
- พอใช้ (50%-69%): สีฟ้า (Light Blue / Sky Blue)
- ต้องปรับปรุง (<50%): สีเหลือง (Yellow)
- เว็บปิด (ผ่าน 0 ข้อ): สีแดง (Red)
"""
import os
import sys
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

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = BASE_DIR / "standards_score_results.xlsx"

# ── Color Definitions ────────────────────────────────────────────────────────
# (Background Hex, Font Hex)
STYLE_MAP = {
    "ดีมาก": {
        "bg": "D4EDDA",  # Soft Green
        "fg": "155724",  # Dark Green
    },
    "ดี": {
        "bg": "CFE2FF",  # Soft Blue (สีน้ำเงิน)
        "fg": "084298",  # Dark Blue
    },
    "พอใช้": {
        "bg": "CFF4FC",  # Soft Cyan/Sky Blue (สีฟ้า)
        "fg": "055160",  # Dark Teal
    },
    "ต้องปรับปรุง": {
        "bg": "FFF3CD",  # Soft Yellow (สีเหลือง)
        "fg": "664D03",  # Dark Amber
    },
    "เว็บปิด": {
        "bg": "F8D7DA",  # Soft Red (สีแดง)
        "fg": "842029",  # Dark Red
    },
}


def main():
    print("=" * 68)
    print("  Applying Custom Colors & Grade Formulas to Excel")
    print("=" * 68)

    if not EXCEL_PATH.exists():
        print(f"[!] File not found: {EXCEL_PATH}")
        sys.exit(1)

    # 1. Backup file
    backup_name = f"standards_score_results_backup_before_colors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    backup_path = BASE_DIR / backup_name
    shutil.copy2(EXCEL_PATH, backup_path)
    print(f"[*] สำรองไฟล์เดิมไว้ที่ -> {backup_name}")

    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["Standards Score Report"]

    total_rows = ws.max_row - 1
    print(f"[*] ปรับแต่งสไตล์และสูตรทั้งหมด {total_rows} เว็บไซต์...")

    for r in range(2, ws.max_row + 1):
        # Determine actual grade based on values
        wcag_p = ws.cell(r, 10).value or 0
        cwv_p = ws.cell(r, 14).value or 0
        ncsa_p = ws.cell(r, 18).value or 0
        owasp_p = ws.cell(r, 22).value or 0
        tot_p = wcag_p + cwv_p + ncsa_p + owasp_p
        status = str(ws.cell(r, 26).value or "").strip()

        pct = tot_p / 71.0

        if tot_p == 0 or "Dead" in status:
            grade_key = "เว็บปิด"
        elif pct >= 0.9:
            grade_key = "ดีมาก"
        elif pct >= 0.7:
            grade_key = "ดี"
        elif pct >= 0.5:
            grade_key = "พอใช้"
        else:
            grade_key = "ต้องปรับปรุง"

        # Update Grade formula in Column E (5)
        # =IF(F{r}=0,"เว็บปิด",IF(D{r}>=0.9,"ดีมาก",IF(D{r}>=0.7,"ดี",IF(D{r}>=0.5,"พอใช้","ต้องปรับปรุง"))))
        formula_grade = f'=IF(F{r}=0,"เว็บปิด",IF(D{r}>=0.9,"ดีมาก",IF(D{r}>=0.7,"ดี",IF(D{r}>=0.5,"พอใช้","ต้องปรับปรุง"))))'
        ws.cell(r, 5).value = formula_grade

        # Apply Colors to Column D (Score %) and Column E (Grade)
        st = STYLE_MAP[grade_key]
        fill = PatternFill(start_color=st["bg"], end_color=st["bg"], fill_type="solid")
        font = Font(name="Segoe UI", size=10, bold=True, color=st["fg"])

        # Col D (คะแนนรวม %)
        cell_d = ws.cell(r, 4)
        cell_d.fill = fill
        cell_d.font = font

        # Col E (ระดับ / Grade)
        cell_e = ws.cell(r, 5)
        cell_e.fill = fill
        cell_e.font = font

    # Update Summary Sheet if exists
    if "สรุปผลมาตรฐาน (Summary)" in wb.sheetnames:
        ws_sum = wb["สรุปผลมาตรฐาน (Summary)"]
        # Update labels and colors in summary
        grades_info = [
            ("ดีมาก", "≥ 90%", STYLE_MAP["ดีมาก"]),
            ("ดี", "70% – 89%", STYLE_MAP["ดี"]),
            ("พอใช้", "50% – 69%", STYLE_MAP["ดี"]),
            ("ต้องปรับปรุง", "< 50%", STYLE_MAP["ต้องปรับปรุง"]),
            ("เว็บปิด", "0%", STYLE_MAP["เว็บปิด"]),
        ]

    wb.save(EXCEL_PATH)
    print(f"[*] บันทึกการเปลี่ยนสีและสูตรลง {EXCEL_PATH.name} เรียบร้อยแล้ว!")
    print("=" * 68)


if __name__ == "__main__":
    main()
