# การเปรียบเทียบเชิงวิชาการ: งานวิจัย Abdulghaffar et al. (2023) กับระบบ WebScan

## 1. ข้อมูลทั่วไป

| รายการ | งานวิจัย (Abdulghaffar et al., 2023) | ระบบ WebScan (โปรเจกต์ปัจจุบัน) |
|--------|--------------------------------------|--------------------------------|
| **ชื่อผลงาน** | Enhancing Web Application Security through Automated Penetration Testing with Multiple Vulnerability Scanners | AI-Assisted Web Standards & Vulnerability Assessment System |
| **ประเภท** | บทความวิจัย (Journal Article — MDPI Computers) | ระบบต้นแบบ (Prototype System) |
| **ปีที่เผยแพร่** | 2023 | 2026 |
| **สถาบัน** | Glasgow Caledonian University, Birmingham City University | — |

---

## 2. วัตถุประสงค์การวิจัย

| ด้าน | งานวิจัย | ระบบ WebScan |
|------|---------|-------------|
| **เป้าหมายหลัก** | พัฒนา framework อัตโนมัติที่รวมผลจาก WAVS หลายตัวเข้าเป็นรายงานเดียว เพื่อพิสูจน์ว่าการใช้หลาย scanner ให้ detection rate ดีกว่าตัวเดียว | พัฒนาระบบประเมินช่องโหว่เว็บไซต์แบบอัตโนมัติ โดยผสานการตรวจจับเทคโนโลยี (Technology Detection), การสแกนช่องโหว่ (Vulnerability Scanning) และการวิเคราะห์ด้วยปัญญาประดิษฐ์ (AI-Assisted Analysis) |
| **คำถามวิจัย** | "How can vulnerability detection rates be improved through the development of an automated framework that combines the results of multiple WAVS into a single vulnerability report?" | (โดยนัย) ระบบ AI-Assisted สามารถให้คำแนะนำด้านความปลอดภัยที่มีคุณภาพจากผลการสแกนแบบอัตโนมัติได้หรือไม่ |
| **ขอบเขต** | เน้นเฉพาะ vulnerability scanning (black-box) | ครอบคลุมทั้ง technology profiling, vulnerability scanning และ AI-driven analysis |

---

## 3. สถาปัตยกรรมระบบ (System Architecture)

### 3.1 งานวิจัย Abdulghaffar et al.

ระบบแบ่งเป็น 3 ส่วนหลัก:

1. **Frontend** — สร้างด้วย React.js ทำหน้าที่เป็น user interface ให้ผู้ใช้กรอก target URL และดูผลลัพธ์
2. **Backend** — สร้างด้วย Node.js + Express.js ทำหน้าที่ประสานงานระหว่าง frontend กับ scanners รวมถึงรัน Combination Algorithm
3. **Scanners** — ใช้ Arachni และ OWASP ZAP ทำงานผ่าน command-line interface (CLI)

การสื่อสารระหว่าง frontend และ backend ใช้ REST API (HTTP GET/POST) โดย backend จะสั่งเริ่ม scanner ทั้ง 2 ตัว รอจนเสร็จ แล้วรวมผลด้วย Combination Algorithm ก่อนส่งกลับ frontend

### 3.2 ระบบ WebScan

ระบบแบ่งเป็น 4 ส่วนหลัก:

1. **Frontend** — สร้างด้วย Next.js + TypeScript ให้ผู้ใช้เลือกประเภทการสแกน (Wappalyzer / ZAP / Both) และแสดงผลลัพธ์พร้อม AI report
2. **Backend** — สร้างด้วย FastAPI (Python) จัดการ REST API, ประสานงาน scanner และเชื่อมต่อ Ollama LLM
3. **Scanners** — ใช้ Wappalyzer (technology detection) และ OWASP ZAP (vulnerability scanning)
4. **AI Engine** — ใช้ Ollama (local LLM) รุ่น llama3.2:3b หรือ qwen2.5:1.5b วิเคราะห์ผลสแกนและสร้างรายงาน

ระบบทั้งหมดถูก containerize ด้วย Docker Compose (services: db, backend, frontend, zap) และใช้ PostgreSQL เก็บประวัติการสแกน

### 3.3 เปรียบเทียบสถาปัตยกรรม

| องค์ประกอบ | งานวิจัย | ระบบ WebScan |
|-----------|---------|-------------|
| **Frontend Framework** | React.js | Next.js (React-based) + TypeScript |
| **Backend Framework** | Node.js + Express.js | FastAPI (Python) |
| **ภาษาหลัก** | JavaScript (ทั้งระบบ) | TypeScript (frontend), Python (backend), JavaScript (scanner script) |
| **ฐานข้อมูล** | ไม่ระบุ | PostgreSQL (เก็บประวัติสแกนทุกครั้ง) |
| **การ deploy** | ไม่ระบุ | Docker Compose (containerized ทุก service) |
| **API Protocol** | REST (HTTP) | REST (HTTP) |

---

## 4. เครื่องมือและเทคโนโลยีที่ใช้

### 4.1 เครื่องมือสแกน (Scanning Tools)

| เครื่องมือ | งานวิจัย | ระบบ WebScan | หมายเหตุ |
|-----------|---------|-------------|---------|
| **OWASP ZAP** | ✅ ใช้ | ✅ ใช้ | ทั้ง 2 ระบบใช้ ZAP เป็น vulnerability scanner หลัก |
| **Arachni** | ✅ ใช้ | ❌ ไม่ใช้ | Arachni ถูก archive บน GitHub แล้ว ไม่มีการอัปเดตต่อ |
| **Wappalyzer** | ❌ ไม่ใช้ | ✅ ใช้ | ใช้ตรวจจับ technology stack ของเว็บเป้าหมาย |
| **Ollama (LLM)** | ❌ ไม่ใช้ | ✅ ใช้ | ใช้ AI วิเคราะห์ผลสแกนและสร้างรายงานแนะนำ |

### 4.2 มาตรฐานอ้างอิง (Security Standards)

| มาตรฐาน | งานวิจัย | ระบบ WebScan |
|---------|---------|-------------|
| **OWASP Top 10 2021** | ✅ ใช้เป็นหลัก (เน้น A01–A06) | ❌ ยังไม่มี explicit mapping |
| **CWE (Common Weakness Enumeration)** | ✅ ใช้ CWE ID จัดกลุ่มผลลัพธ์ | ✅ ใช้ผ่าน ZAP alerts (มี cweid ใน response) แต่ยังไม่ได้จับกลุ่ม |

### 4.3 Benchmark Targets

| Target | งานวิจัย | ระบบ WebScan |
|--------|---------|-------------|
| **OWASP Juice Shop** (39 ช่องโหว่) | ✅ ใช้ทดสอบ | ❌ ยังไม่มีการทดสอบเป็นทางการ |
| **NodeGoat** (17 ช่องโหว่) | ✅ ใช้ทดสอบ | ❌ ยังไม่มีการทดสอบเป็นทางการ |
| **WAVS Framework ตัวเอง** (6 ช่องโหว่) | ✅ ใช้ทดสอบ | ❌ — |

---

## 5. ระเบียบวิธีและอัลกอริทึม (Methodology & Algorithms)

### 5.1 งานวิจัย

ใช้ **Iterative Waterfall Model** เป็นกระบวนการพัฒนาระบบ และนำเสนออัลกอริทึม 2 ตัว:

**Algorithm 1 — Combination Algorithm**: รับผลจาก scanner ทั้ง 2 ตัว จัดกลุ่มตาม CWE ID แล้วสร้าง 4 lists:

- **Union List** — ช่องโหว่ทั้งหมดที่ scanner ตัวใดตัวหนึ่งหรือทั้งคู่ตรวจพบ (ใช้เป็นตัวชี้วัดหลัก)
- **Intersection List** — ช่องโหว่ที่ scanner ทั้ง 2 ตัวตรวจพบตรงกัน (ค่า confidence สูง)
- **Scanner-specific Lists** — ผลเฉพาะของแต่ละ scanner (Arachni List, ZAP List)

**Algorithm 2 — Automation Algorithm**: ควบคุมการทำงานอัตโนมัติ โดยวนลูปสั่ง scanner ทุกตัวเริ่มทำงาน → รอจนเสร็จ → ดึงผล → ส่งเข้า Combination Algorithm → สร้างรายงาน

### 5.2 ระบบ WebScan

ใช้การสแกนแบบ parallel (Promise.all) หรือ sequential ตามประเภทที่ผู้ใช้เลือก:

- **Wappalyzer scan**: เรียก subprocess รัน Node.js script → parse ผลเป็น JSON → บันทึกลง database
- **ZAP scan**: เรียก ZAP API (spider → active scan → get alerts) → จัดกลุ่มตาม risk level → บันทึกลง database
- **AI Analysis**: ส่งผลสแกนทั้งหมดไปยัง Ollama LLM พร้อม prompt ที่กำหนด → รับรายงานวิเคราะห์กลับ

### 5.3 เปรียบเทียบระเบียบวิธี

| ด้าน | งานวิจัย | ระบบ WebScan |
|------|---------|-------------|
| **การรวมผลสแกน** | ✅ มี Combination Algorithm (Union/Intersection) จัดกลุ่มตาม CWE ID | ❌ แสดงผลแยกกันเป็น panel (WappalyzerPanel, ZapPanel) ยังไม่มีการรวมผล |
| **การให้คำแนะนำ** | ❌ ไม่มี — แสดงเฉพาะผลที่ตรวจพบ | ✅ ใช้ LLM วิเคราะห์และให้คำแนะนำ (Executive Summary, Recommendations, Risk Score) |
| **การจัดเก็บผล** | ❌ ไม่ระบุการจัดเก็บ | ✅ บันทึกทุกครั้งลง PostgreSQL (ตาราง scans, scan_results) |
| **ความสามารถขยาย** | ✅ ออกแบบ Vulnerability Scanner Abstract Class ไว้สำหรับเพิ่ม scanner | ❌ ยัง hardcode เป็น endpoint แยก (/scan/wappalyzer, /scan/zap) |

---

## 6. ผลลัพธ์และตัวชี้วัด (Results & Metrics)

### 6.1 ตัวชี้วัดที่ใช้ (Evaluation Metrics)

| ตัวชี้วัด | สูตร | งานวิจัย | ระบบ WebScan |
|----------|------|---------|-------------|
| **Precision** | TP / (TP + FP) | ✅ คำนวณ | ❌ ยังไม่ได้คำนวณ |
| **Recall** | TP / (TP + FN) | ✅ คำนวณ | ❌ ยังไม่ได้คำนวณ |
| **F-Measure** | 2 × (Precision × Recall) / (Precision + Recall) | ✅ คำนวณ | ❌ ยังไม่ได้คำนวณ |

### 6.2 ผลการทดลองจากงานวิจัย

**Target: NodeGoat (17 known vulnerabilities)**

| List | Precision | Recall | F-Measure |
|------|-----------|--------|-----------|
| Union List | 63% | 88% | **73%** |
| Intersection List | 100% | 24% | 38% |
| Arachni List | 100% | 18% | 30% |
| OWASP ZAP List | 61% | 82% | 70% |

**Target: Juice Shop (39 known vulnerabilities)**

| List | Precision | Recall | F-Measure |
|------|-----------|--------|-----------|
| Union List | 78% | 18% | **30%** |
| Intersection List | 100% | 5% | 10% |
| Arachni List | 100% | 5% | 10% |
| OWASP ZAP List | 57% | 10% | 17% |

**Target: WAVS Framework (6 known vulnerabilities)**

| List | Precision | Recall | F-Measure |
|------|-----------|--------|-----------|
| Union List | 86% | 100% | **92%** |
| Intersection List | 100% | 83% | 91% |
| Arachni List | 100% | 33% | 50% |
| OWASP ZAP List | 80% | 67% | 73% |

**ข้อสรุปจากงานวิจัย**: Union List ให้ค่า F-Measure สูงสุดในทุก target ยืนยันว่าการใช้ scanner หลายตัวร่วมกันให้ผลดีกว่าการใช้ตัวเดียว

### 6.3 ระบบ WebScan

ยังไม่มีการทดสอบเชิงปริมาณกับ benchmark targets ที่มี known vulnerabilities ผลลัพธ์ปัจจุบันแสดงเป็น risk summary (High / Medium / Low / Informational) จาก ZAP alerts และ technology list จาก Wappalyzer โดยมี AI report เป็น qualitative output

---

## 7. จุดเด่นและจุดด้อย (Strengths & Weaknesses)

### 7.1 งานวิจัย

| จุดเด่น | จุดด้อย |
|---------|---------|
| มี Combination Algorithm ที่พิสูจน์แล้วว่าเพิ่ม detection rate | ใช้ scanner เพียง 2 ตัว |
| มี evaluation metrics ชัดเจน (Precision, Recall, F-Measure) | Arachni ถูก archive แล้ว ไม่มีการอัปเดต |
| ทดสอบกับ benchmark targets ที่มี known vulnerabilities | ไม่มี automated exploit verification |
| Map ผลเข้า OWASP Top 10 อย่างเป็นระบบ | ไม่มีการจัดเก็บผลลัพธ์ (database) |
| ออกแบบ Abstract Class ให้ขยายได้ | ไม่มี AI/ML ช่วยวิเคราะห์ผลลัพธ์ |

### 7.2 ระบบ WebScan

| จุดเด่น | จุดด้อย |
|---------|---------|
| มี AI-Assisted Analysis (LLM) ซึ่งงานวิจัยยังไม่มี | ยังไม่มี Combination Algorithm สำหรับรวมผล |
| มี Technology Detection (Wappalyzer) เสริมข้อมูลให้ AI วิเคราะห์ได้ลึกขึ้น | ยังไม่มี explicit OWASP Top 10 mapping |
| Containerized ด้วย Docker Compose ทำให้ deploy ง่ายและ reproducible | ยังไม่มี evaluation metrics เชิงปริมาณ |
| มี database (PostgreSQL) เก็บประวัติการสแกน | ยังไม่ได้ทดสอบกับ benchmark targets |
| ใช้ stack ทันสมัย (Next.js, FastAPI, TypeScript) | Scanner architecture ยัง hardcode ไม่มี abstract pattern |
| frontend ให้ผู้ใช้เลือกประเภทสแกนได้ (Wappalyzer / ZAP / Both) | Wappalyzer ทำ technology detection ไม่ใช่ vulnerability scanner ตรงๆ |

---

## 8. สิ่งที่สามารถนำมาประยุกต์ใช้ (Applicable Contributions)

จากงานวิจัย Abdulghaffar et al. (2023) มีแนวคิดและเทคนิค 4 ประการที่สามารถนำมาต่อยอดในระบบ WebScan ได้:

### 8.1 Combination Algorithm

นำ Combination Algorithm มาปรับใช้สำหรับรวมผลจาก Wappalyzer และ ZAP (และ scanner อื่นที่อาจเพิ่มในอนาคต) โดยจัดกลุ่มตาม CWE ID สร้าง Union List สำหรับแสดงภาพรวมทั้งหมด และ Intersection List สำหรับระบุช่องโหว่ที่มี confidence สูง เพื่อลด false positives ทั้งนี้ผลที่รวมแล้วยังสามารถส่งต่อให้ AI วิเคราะห์ได้ครบถ้วนขึ้น

### 8.2 OWASP Top 10 Mapping

นำแนวทางการ map ช่องโหว่เข้ากับ OWASP Top 10 2021 มาใช้ โดยใช้ CWE ID ที่มีอยู่แล้วใน ZAP alerts เป็นตัวเชื่อม แสดงผลเป็น dashboard แสดงว่าเว็บเป้าหมายมีช่องโหว่ครอบคลุม OWASP Top 10 กี่หมวด ช่วยให้รายงานมี credibility ในเชิงมาตรฐานสากล

### 8.3 Abstract Scanner Pattern

นำแนวคิด Vulnerability Scanner Abstract Class มาใช้ สร้าง interface มาตรฐานให้ scanner ทุกตัว (scan, get_results, normalize_output) ทำให้สามารถเพิ่ม scanner ใหม่ (เช่น Nuclei, Nikto) ได้โดยไม่ต้องแก้ไข core logic

### 8.4 Evaluation Framework

นำ evaluation framework มาทดสอบระบบ WebScan กับ benchmark targets เดียวกัน (Juice Shop, NodeGoat) คำนวณ Precision, Recall, F-Measure แล้วเปรียบเทียบกับผลในงานวิจัย เพื่อแสดงให้เห็นว่าระบบที่มี AI ช่วยวิเคราะห์ให้ผลลัพธ์เชิงคุณภาพที่ดีขึ้นอย่างไร

---

## 9. บทสรุป

งานวิจัย Abdulghaffar et al. (2023) พิสูจน์ว่าการรวมผลจาก WAVS หลายตัวเข้าด้วยกัน (Union List) ให้ค่า F-Measure สูงกว่าการใช้ scanner ตัวเดียวอย่างสม่ำเสมอในทุก benchmark target ซึ่งเป็นหลักฐานเชิงประจักษ์ที่สนับสนุนแนวคิดพื้นฐานของระบบ WebScan ที่ใช้ scanner หลายตัวเช่นกัน

ในขณะเดียวกัน ระบบ WebScan มีจุดเด่นที่งานวิจัยยังไม่ได้ครอบคลุม โดยเฉพาะการใช้ AI (Large Language Model) วิเคราะห์ผลสแกนและสร้างรายงานพร้อมคำแนะนำ ซึ่งสอดคล้องกับทิศทาง Future Work ที่งานวิจัยได้เสนอไว้ การผสานจุดเด่นของทั้งสองระบบ — Combination Algorithm จากงานวิจัย ร่วมกับ AI Analysis จากระบบ WebScan — จะสามารถสร้างระบบประเมินช่องโหว่ที่มีทั้งความครอบคลุม (coverage) ความน่าเชื่อถือ (confidence) และคุณค่าเชิงวิเคราะห์ (analytical insight) ที่สูงขึ้น
