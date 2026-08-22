"""
standards_guidance.py
Provides Thai explanations (why_th) and actionable remediation guides (remediation_th)
with code examples for all 68 items across 4 web standards:
1. WCAG 2.1 (37 items)
2. Core Web Vitals & SEO (9 items)
3. NCSA / สกมช. (11 items)
4. OWASP Secure Headers (11 items)
"""

GUIDANCE: dict[str, dict[str, str]] = {
    # ═════════════════════════════════════════════════════════════════
    #  1. WCAG 2.1 (37 items)
    # ═════════════════════════════════════════════════════════════════
    "wcag-01": {
        "why_th": "ผู้ใช้ Screen Reader และผู้ใช้ทั่วไปต้องทราบว่ากำลังอยู่หน้าใดของเว็บไซต์ทันทีที่เปิดหน้า",
        "remediation_th": "ใส่แท็ก <title>ชื่อหน้าเว็บ - ชื่อองค์กร</title> ไว้ภายในส่วน <head> ของ HTML",
    },
    "wcag-02": {
        "why_th": "โปรแกรมอ่านจอภาพต้องทราบภาษาของเอกสารเพื่อออกเสียงสังเคราะห์ (TTS) ได้อย่างถูกต้อง",
        "remediation_th": "กำหนดแอตทริบิวต์ lang บนแท็ก <html> เช่น <html lang=\"th\"> หรือ <html lang=\"en\">",
    },
    "wcag-03": {
        "why_th": "รหัสภาษาต้องตรงตามมาตรฐานสากล (BCP 47) เพื่อให้เบราว์เซอร์และ Screen Reader ตีความได้ถูกต้อง",
        "remediation_th": "ใช้รหัสภาษาที่ถูกต้อง เช่น lang=\"th\", lang=\"en\", lang=\"th-TH\", lang=\"en-US\"",
    },
    "wcag-04": {
        "why_th": "การเรียงลำดับหัวข้อ (h1 -> h2 -> h3) ช่วยให้ผู้พิการทางสายตานำทางและเข้าใจโครงสร้างเนื้อหาได้",
        "remediation_th": "จัดลำดับหัวข้อตามลำดับความสำคัญ ไม่ข้ามระดับ (เช่น จาก <h1> ต้องเป็น <h2> ก่อน <h3>)",
    },
    "wcag-05": {
        "why_th": "แท็กรายการ <ul> หรือ <ol> ต้องมีโครงสร้างที่ถูกต้องเพื่อให้โปรแกรมอ่านจอภาพประกาศจำนวนรายการได้",
        "remediation_th": "ตรวจสอบให้ภายใน <ul> หรือ <ol> มีเฉพาะแท็ก <li> เท่านั้น",
    },
    "wcag-06": {
        "why_th": "แท็ก <li> ต้องอยู่ภายใต้แท็กแม่ที่เป็นรายการ <ul> หรือ <ol> เสมอ",
        "remediation_th": "ย้ายแท็ก <li> ให้ไปอยู่ภายใน <ul> หรือ <ol> หรือ <menu>",
    },
    "wcag-07": {
        "why_th": "ผู้ใช้ Screen Reader ต้องทราบเนื้อหาหรือวัตถุประสงค์ของ <iframe> ก่อนตัดสินใจเข้าใช้งาน",
        "remediation_th": "ใส่แอตทริบิวต์ title บน <iframe> เช่น <iframe src=\"...\" title=\"วิดีโอแนะนำองค์กร\"></iframe>",
    },
    "wcag-08": {
        "why_th": "ตารางข้อมูลต้องระบุหัวตาราง (<th>) ให้ชัดเจนเพื่อให้โปรแกรมอ่านจอภาพเชื่อมโยงข้อมูลในเซลล์กับหัวข้อได้",
        "remediation_th": "ใช้แท็ก <th> พร้อมแอตทริบิวต์ scope=\"col\" หรือ scope=\"row\" ในแถว/คอลัมน์หัวตาราง",
    },
    "wcag-09": {
        "why_th": "ช่องกรอกข้อมูลต้องมีป้ายชื่อ (Label) เพื่อให้ผู้ใช้ทราบว่าต้องกรอกข้อมูลอะไร",
        "remediation_th": "ผูก <label for=\"inputId\">ชื่อป้าย</label> กับ <input id=\"inputId\"> หรือใส่ aria-label=\"...\"",
    },
    "wcag-10": {
        "why_th": "ปุ่มส่งข้อมูลที่เป็นรูปภาพต้องมีคำอธิบาย เพื่อให้ผู้ใช้ Screen Reader ทราบการทำงานของปุ่ม",
        "remediation_th": "ใส่ alt บนปุ่มรูปภาพ เช่น <input type=\"image\" src=\"submit.png\" alt=\"ส่งแบบฟอร์ม\">",
    },
    "wcag-11": {
        "why_th": "แอตทริบิวต์ autocomplete ช่วยให้เบราว์เซอร์ช่วยกรอกข้อมูลอัตโนมัติ ลดภาระผู้มีความบกพร่องทางสติปัญญา/กล้ามเนื้อ",
        "remediation_th": "ใส่ค่า autocomplete ที่ถูกต้อง เช่น autocomplete=\"email\", autocomplete=\"tel\", autocomplete=\"name\"",
    },
    "wcag-12": {
        "why_th": "กลุ่มช่องกรอกข้อมูลที่เกี่ยวข้องกัน (เช่น ตัวเลือก Radio) ต้องจัดกลุ่มและระบุชื่อกลุ่มด้วย Legend",
        "remediation_th": "ครอบกลุ่ม input ด้วย <fieldset><legend>หัวข้อกลุ่ม</legend>...</fieldset>",
    },
    "wcag-13": {
        "why_th": "ช่องกรอกข้อมูลไม่ควรมีป้ายกำกับ Label ซ้ำซ้อน ซึ่งอาจทำให้ Screen Reader อ่านข้อมูลสับสน",
        "remediation_th": "กำหนดให้แต่ละช่อง input มี <label> หรือ aria-labelledby เพียงอันเดียวที่ชัดเจน",
    },
    "wcag-14": {
        "why_th": "ผู้พิการทางสายตาพึ่งพาคำอธิบายภาพ (Alt Text) เพื่อเข้าใจความหมายของรูปภาพ",
        "remediation_th": "ใส่ alt=\"คำอธิบายรูปภาพ\" บนแท็ก <img> ทุกรูป (หากเป็นรูปตกแต่งให้ใส่ alt=\"\")",
    },
    "wcag-15": {
        "why_th": "จุดคลิกบนแผนที่รูปภาพ (<area>) ต้องมีคำอธิบายปลายทางของลิงก์",
        "remediation_th": "ใส่ alt=\"ชื่อปลายทางลิงก์\" บนแท็ก <area> ทุกอัน",
    },
    "wcag-16": {
        "why_th": "แท็ก <object> ต้องมีข้อความหรือเนื้อหาสำรองกรณีอุปกรณ์ไม่รองรับการแสดงผลของปลั๊กอิน",
        "remediation_th": "ใส่ข้อความสำรองภายในแท็ก <object> เช่น <object data=\"...\">เนื้อหาสำรอง</object>",
    },
    "wcag-17": {
        "why_th": "ผู้มีความบกพร่องทางการได้ยินต้องการคำบรรยาย (Captions) เพื่อรับชมและเข้าใจเนื้อหาวิดีโอ",
        "remediation_th": "ใส่แท็ก <track kind=\"captions\" src=\"subtitles.vtt\" srclang=\"th\" label=\"ไทย\"> ในแท็ก <video>",
    },
    "wcag-18": {
        "why_th": "ภาพกราฟิก SVG ต้องมีชื่อหรือคำอธิบายที่ Screen Reader เข้าถึงได้",
        "remediation_th": "ใส่ <title>ชื่อภาพ</title> ภายใน <svg> หรือใส่ role=\"img\" aria-label=\"คำอธิบาย\"",
    },
    "wcag-19": {
        "why_th": "ข้อความลิงก์ต้องสื่อความหมายชัดเจน เพื่อให้ผู้ใช้ทราบว่าคลิกแล้วจะไปยังหน้าใด",
        "remediation_th": "หลีกเลี่ยงข้อความ 'คลิกที่นี่' หรือ 'อ่านต่อ' ให้ใช้ข้อความที่ชัดเจน เช่น 'อ่านรายงานประจำปี 2026'",
    },
    "wcag-20": {
        "why_th": "ปุ่มกดต้องมีข้อความกำกับ เพื่อให้ผู้ใช้ Screen Reader และ Keyboard Navigation ทราบหน้าที่ของปุ่ม",
        "remediation_th": "ใส่ข้อความในแท็ก <button> หรือหากเป็นปุ่มไอคอนให้ใส่ aria-label=\"ค้นหา\"",
    },
    "wcag-21": {
        "why_th": "การตั้งค่า tabindex มากกว่า 0 จะทำลายลำดับการกด Tab ตามธรรมชาติของผู้ใช้คีย์บอร์ด",
        "remediation_th": "ใช้เฉพาะ tabindex=\"0\" (เพื่อให้ focus ได้) หรือ tabindex=\"-1\" (ไม่ให้ tab เข้าถึง) หลีกเลี่ยงค่าบวก",
    },
    "wcag-22": {
        "why_th": "ค่า id ในหน้าเว็บต้องไม่ซ้ำกัน เพื่อป้องกันปัญหาการอ้างอิงของ Accessibility API และสคริปต์",
        "remediation_th": "ตรวจสอบและแก้ไขค่า id ในเอกสาร HTML ให้ไม่ซ้ำกันในทุก element",
    },
    "wcag-23": {
        "why_th": "ผู้ใช้คีย์บอร์ดต้องการปุ่มลัดเพื่อข้ามเมนูนำทางด้านบน ไปยังเนื้อหาหลักได้โดยตรง",
        "remediation_th": "ใส่ลิงก์แรกสุดของหน้า: <a href=\"#main-content\" class=\"skip-link\">ข้ามไปยังเนื้อหาหลัก</a>",
    },
    "wcag-24": {
        "why_th": "Element ที่ถูกซ่อนด้วย aria-hidden=\"true\" ต้องไม่สามารถรับ Focus จากคีย์บอร์ดได้",
        "remediation_th": "ใส่ tabindex=\"-1\" บน element ที่มี aria-hidden=\"true\" หรือใส่ display: none / hidden",
    },
    "wcag-25": {
        "why_th": "กล่องเนื้อหาที่มี Scrollbar ต้องสามารถเลื่อนดูได้ด้วยปุ่มลูกศรบนคีย์บอร์ด",
        "remediation_th": "ใส่ tabindex=\"0\" และ role=\"region\" aria-label=\"...\" บน container ที่มี overflow: scroll",
    },
    "wcag-26": {
        "why_th": "ความเปรียบต่างของสีตัวอักษรและพื้นหลังต้องเพียงพอ เพื่อให้ผู้มีปัญหาทางสายตาอ่านได้ชัดเจน",
        "remediation_th": "ปรับ Contrast Ratio ให้ได้อย่างน้อย 4.5:1 สำหรับตัวอักษรปกติ และ 3:1 สำหรับตัวอักษรขนาดใหญ่ (18pt+)",
    },
    "wcag-27": {
        "why_th": "ห้ามล็อกการซูมหน้าจอ เพื่อให้ผู้มีปัญหาทางสายตาสามารถขยายขนาดหน้าจอเพื่ออ่านเนื้อหาได้",
        "remediation_th": "ใน <meta name=\"viewport\"> ให้ลบ user-scalable=no หรือ maximum-scale=1.0 ออก",
    },
    "wcag-28": {
        "why_th": "เว็บไซต์ต้องรองรับทั้งแนวตั้งและแนวนอน เพื่ออำนวยความสะดวกผู้ใช้ที่ยึดอุปกรณ์กับเก้าอี้รถเข็น",
        "remediation_th": "หลีกเลี่ยงการล็อก orientation ด้วย CSS transform หรือ JavaScript บังคับทิศทางหน้าจอ",
    },
    "wcag-29": {
        "why_th": "ผู้ใช้ต้องสามารถปรับแต่งระยะห่างตัวอักษร (Line Height, Letter Spacing) เพื่อให้อ่านง่ายขึ้นได้โดยเนื้อหาไม่พัง",
        "remediation_th": "หลีกเลี่ยงการล็อกความสูงของกล่องข้อความแบบ fixed height และไม่ใช้ !important ทับระยะห่าง",
    },
    "wcag-30": {
        "why_th": "ค่า ARIA Role ต้องถูกต้องตามมาตรฐาน W3C เพื่อให้โปรแกรมอ่านจอภาพเข้าใจชนิดของ Component",
        "remediation_th": "ตรวจสอบค่า role ให้อยู่ในมาตรฐาน เช่น role=\"button\", role=\"dialog\", role=\"navigation\"",
    },
    "wcag-31": {
        "why_th": "ชื่อแอตทริบิวต์ ARIA ต้องสะกดถูกต้องตามข้อกำหนด W3C ARIA",
        "remediation_th": "ตรวจสอบชื่อ attribute เช่น aria-label, aria-expanded, aria-hidden (ห้ามสะกดผิด)",
    },
    "wcag-32": {
        "why_th": "ค่าของ ARIA Attribute ต้องถูกต้องตาม Type ที่กำหนด (เช่น boolean หรือ id reference)",
        "remediation_th": "กำหนดค่าให้ถูกต้อง เช่น aria-expanded=\"true\" (ไม่ใช่ yes/no), aria-hidden=\"false\"",
    },
    "wcag-33": {
        "why_th": "บาง ARIA Role มีแอตทริบิวต์บังคับที่จำเป็นต้องใส่เพื่อให้ทำงานได้อย่างสมบูรณ์",
        "remediation_th": "เช่น role=\"slider\" ต้องมี aria-valuenow, aria-valuemin, aria-valuemax ให้ครบ",
    },
    "wcag-34": {
        "why_th": "บาง ARIA Role จำเป็นต้องอยู่ภายใต้ Parent Role ที่สัมพันธ์กันตามโครงสร้าง",
        "remediation_th": "เช่น role=\"tab\" ต้องอยู่ภายใต้ role=\"tablist\", role=\"menuitem\" ต้องอยู่ใต้ role=\"menu\"",
    },
    "wcag-35": {
        "why_th": "บาง ARIA Role จำเป็นต้องมี Children Role ที่สัมพันธ์กันภายใน",
        "remediation_th": "เช่น role=\"tablist\" ต้องมีลูกเป็น role=\"tab\", role=\"list\" ต้องมีลูกเป็น role=\"listitem\"",
    },
    "wcag-36": {
        "why_th": "การใส่ aria-hidden=\"true\" บนแท็ก <body> จะทำให้ Screen Reader ซ่อนหน้าเว็บทั้งหมด",
        "remediation_th": "ลบ aria-hidden=\"true\" ออกจากแท็ก <body> หรือ <html>",
    },
    "wcag-37": {
        "why_th": "หน้าต่าง Pop-up หรือ Dialog ต้องมีชื่อกำกับเพื่อให้ผู้ใช้ทราบว่าเป็นกล่องข้อความเรื่องใด",
        "remediation_th": "ใส่ aria-labelledby=\"dialogTitleId\" หรือ aria-label=\"หัวข้อกล่องข้อความ\" บนแท็กที่มี role=\"dialog\"",
    },

    # ═════════════════════════════════════════════════════════════════
    #  2. Core Web Vitals & SEO (9 items)
    # ═════════════════════════════════════════════════════════════════
    "cwv-01": {
        "why_th": "LCP วัดความเร็วในการโหลดองค์ประกอบหลักของหน้าเว็บ (ควรต่ำกว่า 2.5 วินาที)",
        "remediation_th": "บีบอัดรูปภาพเป็น WebP/AVIF, ใช้ <link rel=\"preload\"> กับรูปแบนเนอร์หลัก, ใช้ CDN และเปิด Cache",
    },
    "cwv-02": {
        "why_th": "INP/TBT วัดความหน่วงในการตอบสนองต่อการคลิกหรือสัมผัสของผู้ใช้ (ควรต่ำกว่า 200ms)",
        "remediation_th": "แยก Code Spliting ของ JavaScript, ลดการรัน Third-party Script ที่ไม่จำเป็น, ใช้ Web Worker",
    },
    "cwv-03": {
        "why_th": "CLS วัดการขยับเขยื้อนของเลย์เอาต์ขณะโหลดหน้าเว็บ (ควรต่ำกว่า 0.1)",
        "remediation_th": "กำหนด width และ height บนแท็ก <img> และ <iframe> ทุกตัว, สำรองพื้นที่สำหรับโฆษณาด้วย CSS aspect-ratio",
    },
    "cwv-04": {
        "why_th": "Title และ Meta Description ช่วยให้ Search Engine แสดงผลตัวอย่างหน้าเว็บได้อย่างถูกต้องและดึงดูดผู้ใช้",
        "remediation_th": "ใส่ <title> (ความยาว 50-60 ตัวอักษร) และ <meta name=\"description\" content=\"...\"> (120-160 ตัวอักษร)",
    },
    "cwv-05": {
        "why_th": "Search Engine ต้องได้รับอนุญาตให้เข้ามาจัดเก็บข้อมูล (Crawl & Index) หน้าเว็บได้",
        "remediation_th": "ตรวจสอบไฟล์ robots.txt และแท็ก <meta name=\"robots\"> ว่าไม่ได้ตั้งค่า noindex / Disallow โดยไม่ตั้งใจ",
    },
    "cwv-06": {
        "why_th": "บอทค้นหาต้องสามารถติดตามลิงก์ในหน้าเว็บเพื่อจัดทำดัชนีหน้าอื่นๆ ได้อย่างสมบูรณ์",
        "remediation_th": "ใช้แท็ก <a href=\"/url-path\"> ที่มี URL ปลายทางจริง หลีกเลี่ยงการใช้ <a onclick=\"...\"> หรือ <a href=\"#\">",
    },
    "cwv-07": {
        "why_th": "Canonical URL ป้องกันปัญหาเนื้อหาซ้ำซ้อน (Duplicate Content) จากหลาย URL ที่มีเนื้อหาเดียวกัน",
        "remediation_th": "ใส่ <link rel=\"canonical\" href=\"https://example.com/canonical-path\"> ในส่วน <head>",
    },
    "cwv-08": {
        "why_th": "ปุ่มและลิงก์บนหน้าจอมือถือต้องมีขนาดใหญ่พอและมีระยะห่างที่นิ้วสัมผัสได้ง่าย (อย่างน้อย 48x48px)",
        "remediation_th": "กำหนดขนาดปุ่ม min-width: 48px; min-height: 48px; พร้อม margin เว้นระยะห่างระหว่างปุ่ม",
    },
    "cwv-09": {
        "why_th": "Structured Data (Schema.org) ช่วยให้ Search Engine เข้าใจประเภทข้อมูลและแสดง Rich Snippets ในผลการค้นหา",
        "remediation_th": "ใส่ข้อมูลโครงสร้าง JSON-LD ใน <head> เช่น <script type=\"application/ld+json\">{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", ...}</script>",
    },

    # ═════════════════════════════════════════════════════════════════
    #  3. NCSA / สกมช. (11 items)
    # ═════════════════════════════════════════════════════════════════
    "ncsa-01": {
        "why_th": "บังคับเข้ารหัสข้อมูล 100% ป้องกันการดักฟังรหัสผ่านและข้อมูลส่วนบุคคลตามเกณฑ์มาตรฐาน สกมช.",
        "remediation_th": "ตั้งค่าบน Nginx/Apache ให้ทำ 301 Permanent Redirect จาก HTTP พอร์ต 80 ไปยัง HTTPS พอร์ต 443",
    },
    "ncsa-02": {
        "why_th": "HSTS สั่งให้เบราว์เซอร์จดจำและเชื่อมต่อด้วย HTTPS เสมอ ป้องกันการโจมตีแบบ SSL Stripping",
        "remediation_th": "เพิ่ม HTTP Header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
    },
    "ncsa-03": {
        "why_th": "ป้องกันผู้ไม่หวังดีนำหน้าเว็บไปสร้างภาพซ้อนใน iframe เพื่อหลอกให้ผู้ใช้คลิกทำธุรกรรมโดยไม่รู้ตัว (Clickjacking)",
        "remediation_th": "ตั้งค่า Header: X-Frame-Options: SAMEORIGIN หรือใช้ Content-Security-Policy: frame-ancestors 'self'",
    },
    "ncsa-04": {
        "why_th": "การเปิดเผยยี่ห้อและเวอร์ชันของ Web Server ช่วยให้ผู้โจมตีค้นหาช่องโหว่เฉพาะของเวอร์ชันนั้นได้ง่ายขึ้น",
        "remediation_th": "ตั้งค่าบน Nginx: server_tokens off; หรือบน Apache: ServerTokens Prod และ ServerSignature Off",
    },
    "ncsa-05": {
        "why_th": "โปรโตคอล TLS เวอร์ชันเก่า (SSLv3, TLS 1.0, 1.1) มีช่องโหว่ร้ายแรง ต้องใช้เฉพาะ TLS 1.2 หรือ TLS 1.3",
        "remediation_th": "ตั้งค่าบน Web Server: ssl_protocols TLSv1.2 TLSv1.3; (ปิดการใช้งานเวอร์ชันเก่าทั้งหมด)",
    },
    "ncsa-06": {
        "why_th": "ชุดรหัสเข้ารหัส (Cipher Suite) ต้องแข็งแรง ป้องกันการถอดรหัสข้อมูลจากการดักฟังเครือข่าย",
        "remediation_th": "ใช้ชุดรหัสมาตรฐานสมัยใหม่ เช่น ECDHE-ECDSA-AES128-GCM-SHA256, ECDHE-RSA-AES128-GCM-SHA256 ปิด RC4/3DES/DES",
    },
    "ncsa-07": {
        "why_th": "ช่องโหว่ XSS และ SQL Injection เป็นภัยคุกคามอันดับต้นที่ทำให้ระบบถูกยึดครองหรือข้อมูลลูกค้ารั่วไหล",
        "remediation_th": "ใช้ Parameterized Queries (Prepared Statements), ทำ Input Sanitization/Validation และติดตั้ง WAF",
    },
    "ncsa-08": {
        "why_th": "Cookie ที่เก็บ Session หรือ Token สำคัญต้องเปิด Flag ป้องกันการถูกขโมยผ่านสคริปต์หรือเครือข่ายไม่ปลอดภัย",
        "remediation_th": "ตั้งค่า Cookie ให้มี Flags ครบ: Set-Cookie: sessionId=...; Secure; HttpOnly; SameSite=Lax",
    },
    "ncsa-09": {
        "why_th": "การเปิดเผยชื่อและเวอร์ชันของ Framework/CMS ช่วยให้ผู้โจมตีเจาะระบบด้วย Exploit สำเร็จรูป",
        "remediation_th": "ลบ Header X-Powered-By และ meta generator tags ใน HTML (เช่น <meta name=\"generator\" ...>)",
    },
    "ncsa-10": {
        "why_th": "ซอฟต์แวร์และปลั๊กอินที่มีช่องโหว่ตามฐานข้อมูล CVE ต้องได้รับการอัปเดต Patch ความปลอดภัยทันที",
        "remediation_th": "ตรวจสอบและอัปเดตเวอร์ชันของ CMS, ปลั๊กอิน, ไลบรารี และระบบปฏิบัติการให้เป็นเวอร์ชันล่าสุดที่มี Security Patch",
    },
    "ncsa-11": {
        "why_th": "หน้าเข้าสู่ระบบของผู้ดูแลระบบ (/admin, /wp-admin) ไม่ควรเปิดให้บุคคลทั่วไปจากอินเทอร์เน็ตเข้าถึงได้โดยตรง",
        "remediation_th": "จำกัดการเข้าถึงหน้าจัดการด้วย IP Whitelist, กำหนดให้เข้าผ่าน VPN ภายในองค์กร และเปิดใช้ 2FA",
    },

    # ═════════════════════════════════════════════════════════════════
    #  4. OWASP HTTP Security Headers (11 items)
    # ═════════════════════════════════════════════════════════════════
    "owasp-01": {
        "why_th": "Content-Security-Policy (CSP) เป็นเกราะป้องกัน XSS และ Data Injection ที่ทรงพลังที่สุด",
        "remediation_th": "เพิ่ม Header: Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; script-src 'self'; style-src 'self' 'unsafe-inline';",
    },
    "owasp-02": {
        "why_th": "Strict-Transport-Security (HSTS) ป้องกัน Man-in-the-Middle และการ Downgrade โปรโตคอลเป็น HTTP",
        "remediation_th": "เพิ่ม Header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
    },
    "owasp-03": {
        "why_th": "X-Frame-Options ควบคุมการนำหน้าเว็บไปฝังใน Frame ป้องกันการโจมตีหลอกคลิก Clickjacking",
        "remediation_th": "เพิ่ม Header: X-Frame-Options: SAMEORIGIN (หรือ DENY หากไม่ต้องการให้ฝังใน frame ใดๆ)",
    },
    "owasp-04": {
        "why_th": "X-Content-Type-Options ป้องกันเบราว์เซอร์เดาชนิดไฟล์ (MIME sniffing) ซึ่งอาจนำไปสู่การรันโค้ดอันตราย",
        "remediation_th": "เพิ่ม Header: X-Content-Type-Options: nosniff",
    },
    "owasp-05": {
        "why_th": "Referrer-Policy ควบคุมการส่งข้อมูล URL ต้นทางไปยังเว็บไซต์ภายนอก ป้องกันข้อมูลลับใน Query String รั่วไหล",
        "remediation_th": "เพิ่ม Header: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "owasp-06": {
        "why_th": "Permissions-Policy ควบคุมและจำกัดการเข้าถึงฮาร์ดแวร์ของผู้ใช้ เช่น กล้อง ไมโครโฟน ตำแหน่ง GPS",
        "remediation_th": "เพิ่ม Header: Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()",
    },
    "owasp-07": {
        "why_th": "COOP (Cross-Origin-Opener-Policy) แยกกระบวนการประมวลผลของหน้าเว็บ ป้องกันการโจมตีแบบ Spectre/Cross-Origin",
        "remediation_th": "เพิ่ม Header: Cross-Origin-Opener-Policy: same-origin",
    },
    "owasp-08": {
        "why_th": "COEP (Cross-Origin-Embedder-Policy) บล็อกการโหลดทรัพยากรจากภายนอกที่ไม่ได้รับอนุญาตชัดเจน",
        "remediation_th": "เพิ่ม Header: Cross-Origin-Embedder-Policy: require-corp (หรือ credentialless)",
    },
    "owasp-09": {
        "why_th": "CORP (Cross-Origin-Resource-Policy) ป้องกันเว็บไซต์อื่นดึงรูปภาพ สคริปต์ หรือข้อมูลลับไปใช้งาน",
        "remediation_th": "เพิ่ม Header: Cross-Origin-Resource-Policy: same-origin (หรือ same-site)",
    },
    "owasp-10": {
        "why_th": "Cache-Control ควบคุมการบันทึกสำเนาหน้าเว็บในเบราว์เซอร์ ป้องกันข้อมูลส่วนบุคคลถูกแคชบนเครื่องสาธารณะ",
        "remediation_th": "สำหรับหน้าที่มีข้อมูลสำคัญ ให้เพิ่ม Header: Cache-Control: no-store, max-age=0, must-revalidate",
    },
    "owasp-11": {
        "why_th": "Set-Cookie Attributes ต้องมีคุณสมบัติความปลอดภัยครบถ้วน ป้องกัน Session Hijacking และ CSRF",
        "remediation_th": "กำหนดค่า Cookie ทุกตัวด้วย: Set-Cookie: name=value; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400",
    },
}


def get_guidance(check_id: str) -> dict[str, str]:
    """Return guidance dict for given check_id or defaults."""
    return GUIDANCE.get(check_id, {
        "why_th": "ตรวจสอบความสอดคล้องตามมาตรฐานความปลอดภัยและการใช้งานสากล",
        "remediation_th": "ปรับปรุงโค้ดและโครงสร้างของเว็บไซต์ให้ถูกต้องตามข้อกำหนดมาตรฐาน",
    })
