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
        "why_th": "หากไม่มี <title> ผู้ใช้ Screen Reader จะไม่ทราบว่าอยู่หน้าใด ทำให้สับสนระหว่างแท็บต่างๆ และผู้ใช้ทั่วไปจะเห็น Bookmark ที่ไม่มีชื่อ ส่งผลเสียต่อ SEO เนื่องจาก Google ใช้ Title แสดงผลในหน้าค้นหา",
        "remediation_th": "ใส่แท็ก <title>ชื่อหน้าเว็บ - ชื่อองค์กร</title> ไว้ภายในส่วน <head> ของ HTML",
    },
    "wcag-02": {
        "why_th": "หากไม่ระบุภาษา Screen Reader จะเลือกภาษาผิดในการอ่านออกเสียง เช่น อ่านภาษาไทยด้วยสำเนียงอังกฤษ ทำให้ผู้พิการทางสายตาไม่สามารถเข้าใจเนื้อหาได้ และเบราว์เซอร์จะแปลภาษาอัตโนมัติผิดพลาด",
        "remediation_th": "กำหนดแอตทริบิวต์ lang บนแท็ก <html> เช่น <html lang=\"th\"> หรือ <html lang=\"en\">",
    },
    "wcag-03": {
        "why_th": "หากรหัสภาษาไม่ถูกต้องตาม BCP 47 เบราว์เซอร์และ Screen Reader จะไม่รู้จักภาษา ทำให้การออกเสียง การแปลภาษา และการจัดรูปแบบวันที่/ตัวเลขทำงานผิดพลาดทั้งหมด",
        "remediation_th": "ใช้รหัสภาษาที่ถูกต้อง เช่น lang=\"th\", lang=\"en\", lang=\"th-TH\", lang=\"en-US\"",
    },
    "wcag-04": {
        "why_th": "หากหัวข้อข้ามระดับ (เช่น h1 กระโดดเป็น h4) ผู้ใช้ Screen Reader จะหลงทางในโครงสร้างเนื้อหา ไม่สามารถนำทางด้วยคีย์ลัดหัวข้อได้ และ Search Engine จะตีความลำดับความสำคัญของเนื้อหาผิดพลาด",
        "remediation_th": "จัดลำดับหัวข้อตามลำดับความสำคัญ ไม่ข้ามระดับ (เช่น จาก <h1> ต้องเป็น <h2> ก่อน <h3>)",
    },
    "wcag-05": {
        "why_th": "หากโครงสร้างรายการผิดพลาด Screen Reader จะอ่านจำนวนรายการผิด หรือไม่ประกาศว่าเป็นรายการเลย ทำให้ผู้พิการทางสายตาไม่ทราบว่ามีตัวเลือกกี่รายการ",
        "remediation_th": "ตรวจสอบให้ภายใน <ul> หรือ <ol> มีเฉพาะแท็ก <li> เท่านั้น",
    },
    "wcag-06": {
        "why_th": "หาก <li> ไม่อยู่ในแท็กรายการ Screen Reader จะไม่รู้ว่าเป็นส่วนหนึ่งของรายการ ทำให้อ่านเป็นข้อความธรรมดา ผู้ใช้ไม่สามารถนำทางด้วยคีย์ลัดรายการได้",
        "remediation_th": "ย้ายแท็ก <li> ให้ไปอยู่ภายใน <ul> หรือ <ol> หรือ <menu>",
    },
    "wcag-07": {
        "why_th": "หาก <iframe> ไม่มี title ผู้ใช้ Screen Reader จะเจอ iframe ว่างเปล่าไม่มีคำอธิบาย ไม่ทราบว่าเป็นวิดีโอ แผนที่ หรือแบบฟอร์ม อาจข้ามเนื้อหาสำคัญหรือเสียเวลาเข้าไปสำรวจ iframe ที่ไม่เกี่ยวข้อง",
        "remediation_th": "ใส่แอตทริบิวต์ title บน <iframe> เช่น <iframe src=\"...\" title=\"วิดีโอแนะนำองค์กร\"></iframe>",
    },
    "wcag-08": {
        "why_th": "หากตารางไม่มีหัวตาราง <th> ผู้ใช้ Screen Reader จะได้ยินแค่ตัวเลข/ข้อความในเซลล์โดยไม่ทราบว่าข้อมูลนั้นหมายถึงอะไร เช่น ได้ยิน \"500\" แต่ไม่รู้ว่าเป็นราคา จำนวน หรือรหัส",
        "remediation_th": "ใช้แท็ก <th> พร้อมแอตทริบิวต์ scope=\"col\" หรือ scope=\"row\" ในแถว/คอลัมน์หัวตาราง",
    },
    "wcag-09": {
        "why_th": "หากช่องกรอกไม่มี Label ผู้ใช้ Screen Reader จะไม่ทราบว่าต้องกรอกอะไร อาจกรอกข้อมูลผิดช่อง เช่น ใส่เบอร์โทรในช่องอีเมล ส่งผลให้ข้อมูลที่ได้รับไม่ถูกต้อง",
        "remediation_th": "ผูก <label for=\"inputId\">ชื่อป้าย</label> กับ <input id=\"inputId\"> หรือใส่ aria-label=\"...\"",
    },
    "wcag-10": {
        "why_th": "หากปุ่มรูปภาพไม่มี alt ผู้ใช้ Screen Reader จะไม่ทราบว่าปุ่มทำหน้าที่อะไร อาจกดปุ่มผิดโดยไม่ตั้งใจ เช่น กดลบข้อมูลแทนที่จะกดบันทึก เสี่ยงต่อการสูญเสียข้อมูล",
        "remediation_th": "ใส่ alt บนปุ่มรูปภาพ เช่น <input type=\"image\" src=\"submit.png\" alt=\"ส่งแบบฟอร์ม\">",
    },
    "wcag-11": {
        "why_th": "หาก autocomplete ไม่ถูกต้อง เบราว์เซอร์จะแนะนำข้อมูลผิดประเภท เช่น แนะนำที่อยู่ในช่องเบอร์โทร ผู้พิการทางสติปัญญาหรือกล้ามเนื้อจะเสียเวลาลบและพิมพ์ใหม่ ลดประสิทธิภาพการใช้งาน",
        "remediation_th": "ใส่ค่า autocomplete ที่ถูกต้อง เช่น autocomplete=\"email\", autocomplete=\"tel\", autocomplete=\"name\"",
    },
    "wcag-12": {
        "why_th": "หากกลุ่มตัวเลือก (เช่น Radio Button) ไม่มี <fieldset> และ <legend> ผู้ใช้ Screen Reader จะไม่ทราบว่าตัวเลือกเหล่านั้นเกี่ยวข้องกัน อาจเลือกผิดกลุ่ม เช่น เลือกขนาดเสื้อแทนที่จะเลือกสี",
        "remediation_th": "ครอบกลุ่ม input ด้วย <fieldset><legend>หัวข้อกลุ่ม</legend>...</fieldset>",
    },
    "wcag-13": {
        "why_th": "หากช่องกรอกมี Label ซ้ำซ้อน Screen Reader จะอ่าน Label หลายครั้งหรืออ่านผิด ทำให้ผู้ใช้สับสนว่าต้องกรอกข้อมูลอะไร และอาจทำให้ Accessibility Testing Tools แจ้งผลผิดพลาด",
        "remediation_th": "กำหนดให้แต่ละช่อง input มี <label> หรือ aria-labelledby เพียงอันเดียวที่ชัดเจน",
    },
    "wcag-14": {
        "why_th": "หากรูปภาพไม่มี alt ผู้พิการทางสายตาจะไม่ทราบเนื้อหาของรูป Screen Reader จะอ่านชื่อไฟล์แทน เช่น \"IMG_20240523_001.jpg\" ซึ่งไม่มีความหมาย และหากรูปโหลดไม่ได้ ผู้ใช้ทั่วไปก็จะไม่เห็นคำอธิบายสำรอง",
        "remediation_th": "ใส่ alt=\"คำอธิบายรูปภาพ\" บนแท็ก <img> ทุกรูป (หากเป็นรูปตกแต่งให้ใส่ alt=\"\")",
    },
    "wcag-15": {
        "why_th": "หากจุดคลิกบนแผนที่รูปภาพไม่มี alt ผู้ใช้ Screen Reader จะไม่ทราบว่าแต่ละจุดคลิกไปไหน อาจคลิกไปยังหน้าที่ไม่ต้องการหรือพลาดลิงก์สำคัญไป",
        "remediation_th": "ใส่ alt=\"ชื่อปลายทางลิงก์\" บนแท็ก <area> ทุกอัน",
    },
    "wcag-16": {
        "why_th": "หาก <object> ไม่มีเนื้อหาสำรอง อุปกรณ์ที่ไม่รองรับปลั๊กอินนั้น (เช่น มือถือบางรุ่น) จะแสดงพื้นที่ว่างเปล่า ผู้ใช้จะเสียเนื้อหาสำคัญโดยไม่รู้ตัว",
        "remediation_th": "ใส่ข้อความสำรองภายในแท็ก <object> เช่น <object data=\"...\">เนื้อหาสำรอง</object>",
    },
    "wcag-17": {
        "why_th": "หากวิดีโอไม่มีคำบรรยาย (Captions) ผู้พิการทางการได้ยินจะไม่สามารถเข้าถึงเนื้อหาวิดีโอได้เลย และผู้ใช้ในสภาพแวดล้อมที่เปิดเสียงไม่ได้ (เช่น ห้องสมุด ขนส่งสาธารณะ) ก็จะพลาดข้อมูลสำคัญ",
        "remediation_th": "ใส่แท็ก <track kind=\"captions\" src=\"subtitles.vtt\" srclang=\"th\" label=\"ไทย\"> ในแท็ก <video>",
    },
    "wcag-18": {
        "why_th": "หาก SVG ไม่มี <title> หรือ aria-label ผู้ใช้ Screen Reader จะข้ามภาพนั้นไป หากเป็นไอคอนที่สื่อความหมาย (เช่น ไอคอนเตือนภัย ไอคอนสถานะ) ผู้ใช้จะพลาดข้อมูลสำคัญ",
        "remediation_th": "ใส่ <title>ชื่อภาพ</title> ภายใน <svg> หรือใส่ role=\"img\" aria-label=\"คำอธิบาย\"",
    },
    "wcag-19": {
        "why_th": "หากลิงก์มีข้อความว่า 'คลิกที่นี่' หรือ 'อ่านต่อ' ผู้ใช้ Screen Reader ที่นำทางด้วยรายการลิงก์จะเห็นแต่ 'คลิกที่นี่' ซ้ำๆ ไม่ทราบว่าแต่ละลิงก์ไปที่ไหน ทำให้สูญเสียความสามารถในการนำทาง",
        "remediation_th": "หลีกเลี่ยงข้อความ 'คลิกที่นี่' หรือ 'อ่านต่อ' ให้ใช้ข้อความที่ชัดเจน เช่น 'อ่านรายงานประจำปี 2026'",
    },
    "wcag-20": {
        "why_th": "หากปุ่มไม่มีข้อความกำกับ ผู้ใช้ Screen Reader จะได้ยินแค่ 'ปุ่ม' โดยไม่ทราบว่าทำหน้าที่อะไร อาจกดปุ่มลบข้อมูลแทนปุ่มบันทึก หรือข้ามปุ่มสำคัญไปโดยไม่รู้ตัว",
        "remediation_th": "ใส่ข้อความในแท็ก <button> หรือหากเป็นปุ่มไอคอนให้ใส่ aria-label=\"ค้นหา\"",
    },
    "wcag-21": {
        "why_th": "หากใช้ tabindex มากกว่า 0 ลำดับการกด Tab จะไม่ตรงกับลำดับที่มองเห็น ทำให้ผู้ใช้คีย์บอร์ดกด Tab แล้ว Focus กระโดดไปมาอย่างสับสน ส่งผลให้กรอกฟอร์มผิดลำดับหรือข้ามช่องสำคัญ",
        "remediation_th": "ใช้เฉพาะ tabindex=\"0\" (เพื่อให้ focus ได้) หรือ tabindex=\"-1\" (ไม่ให้ tab เข้าถึง) หลีกเลี่ยงค่าบวก",
    },
    "wcag-22": {
        "why_th": "หาก id ซ้ำกัน JavaScript และ Accessibility API จะอ้างอิงผิด element เช่น label ชี้ไปยัง input ผิดช่อง ทำให้ฟอร์มทำงานผิดพลาดและ Screen Reader อ่านข้อมูลผิด",
        "remediation_th": "ตรวจสอบและแก้ไขค่า id ในเอกสาร HTML ให้ไม่ซ้ำกันในทุก element",
    },
    "wcag-23": {
        "why_th": "หากไม่มี Skip Link ผู้ใช้คีย์บอร์ดต้องกด Tab ผ่านเมนูนำทางทั้งหมด (อาจ 20-50 ลิงก์) ทุกครั้งที่เปลี่ยนหน้า ทำให้เสียเวลาอย่างมากและเกิดอาการล้าจากการกดซ้ำๆ",
        "remediation_th": "ใส่ลิงก์แรกสุดของหน้า: <a href=\"#main-content\" class=\"skip-link\">ข้ามไปยังเนื้อหาหลัก</a>",
    },
    "wcag-24": {
        "why_th": "หาก element ที่ซ่อนด้วย aria-hidden ยังรับ Focus ได้ ผู้ใช้คีย์บอร์ดจะ Focus ไปยัง element ที่มองไม่เห็น ทำให้สับสนว่า Focus หายไปไหน และอาจกดปุ่มที่ซ่อนอยู่โดยไม่ตั้งใจ",
        "remediation_th": "ใส่ tabindex=\"-1\" บน element ที่มี aria-hidden=\"true\" หรือใส่ display: none / hidden",
    },
    "wcag-25": {
        "why_th": "หากกล่อง Scroll ไม่สามารถเลื่อนด้วยคีย์บอร์ดได้ ผู้ใช้ที่ไม่สามารถใช้เมาส์จะถูกบล็อกจากเนื้อหาภายใน ไม่สามารถอ่านข้อมูลทั้งหมดได้ เสมือนเนื้อหาส่วนนั้นไม่มีอยู่",
        "remediation_th": "ใส่ tabindex=\"0\" และ role=\"region\" aria-label=\"...\" บน container ที่มี overflow: scroll",
    },
    "wcag-26": {
        "why_th": "หากความเปรียบต่างสีไม่เพียงพอ ผู้ที่ตาบอดสีหรือสายตาเลือนรางจะอ่านข้อความไม่ออก ส่งผลให้ผู้ใช้ประมาณ 8% ของประชากรชาย และผู้สูงอายุไม่สามารถใช้งานเว็บไซต์ได้",
        "remediation_th": "ปรับ Contrast Ratio ให้ได้อย่างน้อย 4.5:1 สำหรับตัวอักษรปกติ และ 3:1 สำหรับตัวอักษรขนาดใหญ่ (18pt+)",
    },
    "wcag-27": {
        "why_th": "หากล็อกการซูม ผู้ที่สายตาเลือนรางจะไม่สามารถขยายหน้าจอเพื่ออ่านเนื้อหาได้ ถือเป็นการปิดกั้นการเข้าถึงเว็บไซต์สำหรับผู้พิการทางสายตาโดยตรง ซึ่งอาจผิดกฎหมายการเข้าถึงในหลายประเทศ",
        "remediation_th": "ใน <meta name=\"viewport\"> ให้ลบ user-scalable=no หรือ maximum-scale=1.0 ออก",
    },
    "wcag-28": {
        "why_th": "หากล็อกทิศทางหน้าจอ ผู้ใช้ที่ยึดอุปกรณ์กับเก้าอี้รถเข็น (ติดแนวนอนถาวร) จะไม่สามารถใช้งานเว็บไซต์ได้เลย ถือเป็นการปิดกั้นการเข้าถึงอย่างร้ายแรง",
        "remediation_th": "หลีกเลี่ยงการล็อก orientation ด้วย CSS transform หรือ JavaScript บังคับทิศทางหน้าจอ",
    },
    "wcag-29": {
        "why_th": "หากล็อกระยะห่างตัวอักษรด้วย !important ผู้ใช้ที่มีปัญหาการอ่าน (Dyslexia) จะไม่สามารถปรับแต่ง Line Height และ Letter Spacing เพื่อให้อ่านง่ายขึ้นได้ ข้อความอาจทับซ้อนกันจนอ่านไม่ออก",
        "remediation_th": "หลีกเลี่ยงการล็อกความสูงของกล่องข้อความแบบ fixed height และไม่ใช้ !important ทับระยะห่าง",
    },
    "wcag-30": {
        "why_th": "หาก ARIA Role ไม่ถูกต้อง Screen Reader จะประกาศชนิด element ผิด เช่น ประกาศลิงก์ว่าเป็นปุ่ม ทำให้ผู้ใช้กดแล้วไม่เกิดผลตามที่คาดหวัง และเสียความน่าเชื่อถือของ Accessibility",
        "remediation_th": "ตรวจสอบค่า role ให้อยู่ในมาตรฐาน เช่น role=\"button\", role=\"dialog\", role=\"navigation\"",
    },
    "wcag-31": {
        "why_th": "หากชื่อ ARIA Attribute สะกดผิด (เช่น aria-lable แทน aria-label) เบราว์เซอร์จะเพิกเฉย attribute นั้นทั้งหมด ทำให้ Screen Reader ไม่ได้รับข้อมูลสำคัญและ element นั้นกลายเป็นเข้าถึงไม่ได้",
        "remediation_th": "ตรวจสอบชื่อ attribute เช่น aria-label, aria-expanded, aria-hidden (ห้ามสะกดผิด)",
    },
    "wcag-32": {
        "why_th": "หากค่า ARIA ไม่ตรงตาม Type ที่กำหนด (เช่น aria-expanded=\"yes\" แทน \"true\") เบราว์เซอร์จะไม่รู้จักสถานะนั้น ทำให้ Screen Reader ไม่ประกาศสถานะเปิด/ปิดของเมนูหรือ Accordion",
        "remediation_th": "กำหนดค่าให้ถูกต้อง เช่น aria-expanded=\"true\" (ไม่ใช่ yes/no), aria-hidden=\"false\"",
    },
    "wcag-33": {
        "why_th": "หากขาด ARIA Attribute บังคับ เช่น slider ไม่มี aria-valuenow Screen Reader จะไม่สามารถบอกค่าปัจจุบันของตัวเลื่อนได้ ผู้ใช้จะปรับค่าโดยไม่ทราบว่าเลื่อนไปถึงจุดไหนแล้ว",
        "remediation_th": "เช่น role=\"slider\" ต้องมี aria-valuenow, aria-valuemin, aria-valuemax ให้ครบ",
    },
    "wcag-34": {
        "why_th": "หาก ARIA Role ไม่อยู่ภายใต้ Parent ที่กำหนด (เช่น tab อยู่นอก tablist) Screen Reader จะไม่รู้ว่า element เหล่านี้เกี่ยวข้องกัน ทำให้คีย์ลัด Tab Navigation ไม่ทำงาน",
        "remediation_th": "เช่น role=\"tab\" ต้องอยู่ภายใต้ role=\"tablist\", role=\"menuitem\" ต้องอยู่ใต้ role=\"menu\"",
    },
    "wcag-35": {
        "why_th": "หาก ARIA Role ขาด Children ที่สัมพันธ์กัน (เช่น tablist ไม่มี tab) Screen Reader จะประกาศว่ามี tablist แต่ไม่พบ tab ใดๆ ทำให้ผู้ใช้สับสนและคิดว่า component เสีย",
        "remediation_th": "เช่น role=\"tablist\" ต้องมีลูกเป็น role=\"tab\", role=\"list\" ต้องมีลูกเป็น role=\"listitem\"",
    },
    "wcag-36": {
        "why_th": "หากใส่ aria-hidden=\"true\" บน <body> Screen Reader จะซ่อนหน้าเว็บทั้งหมด ผู้พิการทางสายตาจะไม่สามารถเข้าถึงเนื้อหาใดๆ บนหน้าเว็บได้เลย เสมือนหน้าว่างเปล่า",
        "remediation_th": "ลบ aria-hidden=\"true\" ออกจากแท็ก <body> หรือ <html>",
    },
    "wcag-37": {
        "why_th": "หาก Dialog/Popup ไม่มีชื่อกำกับ ผู้ใช้ Screen Reader จะไม่ทราบว่า Popup นี้เกี่ยวกับอะไร อาจปิดทิ้งโดยไม่อ่านข้อความสำคัญ เช่น คำเตือนก่อนลบข้อมูล หรือข้อตกลงการใช้บริการ",
        "remediation_th": "ใส่ aria-labelledby=\"dialogTitleId\" หรือ aria-label=\"หัวข้อกล่องข้อความ\" บนแท็กที่มี role=\"dialog\"",
    },

    # ═════════════════════════════════════════════════════════════════
    #  2. Core Web Vitals & SEO (9 items)
    # ═════════════════════════════════════════════════════════════════
    "cwv-01": {
        "why_th": "หาก LCP ช้าเกิน 2.5 วินาที ผู้ใช้ 53% จะกดปิดเว็บทันที ส่งผลให้สูญเสียผู้เข้าชม และ Google จะลดอันดับเว็บไซต์ในผลค้นหา ธุรกิจสูญเสียรายได้จากการที่ลูกค้าเข้าไม่ถึง",
        "remediation_th": "บีบอัดรูปภาพเป็น WebP/AVIF, ใช้ <link rel=\"preload\"> กับรูปแบนเนอร์หลัก, ใช้ CDN และเปิด Cache",
    },
    "cwv-02": {
        "why_th": "หาก TBT/INP สูง (หน่วงเกิน 200ms) ผู้ใช้จะรู้สึกว่าเว็บค้าง กดปุ่มแล้วไม่เกิดอะไร อาจกดซ้ำหลายครั้งจนเกิดการส่งฟอร์มซ้ำ หรือทำธุรกรรมซ้ำ ส่งผลเสียต่อ UX และรายได้",
        "remediation_th": "แยก Code Spliting ของ JavaScript, ลดการรัน Third-party Script ที่ไม่จำเป็น, ใช้ Web Worker",
    },
    "cwv-03": {
        "why_th": "หาก CLS สูง (เกิน 0.1) เลย์เอาต์จะกระโดดระหว่างโหลด ผู้ใช้อาจกดปุ่มผิดเพราะ element ขยับหนี เช่น กดปุ่ม 'ยกเลิก' แทน 'ยืนยัน' เนื่องจากโฆษณาดันเลย์เอาต์",
        "remediation_th": "กำหนด width และ height บนแท็ก <img> และ <iframe> ทุกตัว, สำรองพื้นที่สำหรับโฆษณาด้วย CSS aspect-ratio",
    },
    "cwv-04": {
        "why_th": "หากไม่มี Title และ Meta Description Search Engine จะสร้างข้อความสรุปเอง ซึ่งมักไม่ตรงกับเนื้อหาจริง ทำให้ CTR ต่ำ ผู้ใช้ไม่คลิกเข้ามา แม้เว็บจะมีเนื้อหาดีก็ไม่มีคนเห็น",
        "remediation_th": "ใส่ <title> (ความยาว 50-60 ตัวอักษร) และ <meta name=\"description\" content=\"...\"> (120-160 ตัวอักษร)",
    },
    "cwv-05": {
        "why_th": "หาก robots.txt บล็อก Googlebot หรือมี meta noindex เว็บจะหายจากผลค้นหาของ Google ทั้งหมด ไม่มีใครค้นหาเจอ เสมือนเว็บไม่มีอยู่บนอินเทอร์เน็ต",
        "remediation_th": "ตรวจสอบไฟล์ robots.txt และแท็ก <meta name=\"robots\"> ว่าไม่ได้ตั้งค่า noindex / Disallow โดยไม่ตั้งใจ",
    },
    "cwv-06": {
        "why_th": "หากลิงก์ใช้ <a href=\"#\"> หรือ <a onclick=\"...\"> บอท Search Engine จะไม่สามารถติดตามลิงก์ไปยังหน้าอื่นได้ ทำให้หน้าเว็บภายในไม่ถูกจัดทำดัชนี สูญเสียโอกาสติดอันดับ",
        "remediation_th": "ใช้แท็ก <a href=\"/url-path\"> ที่มี URL ปลายทางจริง หลีกเลี่ยงการใช้ <a onclick=\"...\"> หรือ <a href=\"#\">",
    },
    "cwv-07": {
        "why_th": "หากไม่มี Canonical URL และเว็บมีหลาย URL ที่แสดงเนื้อหาเดียวกัน Google จะมองเป็น Duplicate Content และกระจาย SEO Power ไปคนละหน้า ทำให้ทุกหน้าติดอันดับต่ำ",
        "remediation_th": "ใส่ <link rel=\"canonical\" href=\"https://example.com/canonical-path\"> ในส่วน <head>",
    },
    "cwv-08": {
        "why_th": "หากปุ่มเล็กเกินไปหรือชิดกันบนมือถือ ผู้ใช้จะกดผิดปุ่มบ่อยๆ เช่น กดลิงก์โฆษณาแทนปุ่ม 'อ่านต่อ' ทำให้ผู้ใช้หงุดหงิดและออกจากเว็บ Bounce Rate สูงขึ้น",
        "remediation_th": "กำหนดขนาดปุ่ม min-width: 48px; min-height: 48px; พร้อม margin เว้นระยะห่างระหว่างปุ่ม",
    },
    "cwv-09": {
        "why_th": "หากไม่มี Structured Data (Schema.org) เว็บจะไม่ได้แสดง Rich Snippets ในผลค้นหา (เช่น ดาว Rating รูปภาพ ราคา) ซึ่งเว็บที่มี Rich Snippets มี CTR สูงกว่า 20-30%",
        "remediation_th": "ใส่ข้อมูลโครงสร้าง JSON-LD ใน <head> เช่น <script type=\"application/ld+json\">{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", ...}</script>",
    },

    # ═════════════════════════════════════════════════════════════════
    #  3. NCSA / สกมช. (11 items)
    # ═════════════════════════════════════════════════════════════════
    "ncsa-01": {
        "why_th": "หากไม่บังคับ HTTPS แฮกเกอร์ที่อยู่บนเครือข่ายเดียวกัน (เช่น WiFi สาธารณะ) สามารถดักจับข้อมูลทุกอย่างที่ผู้ใช้ส่ง รวมถึงรหัสผ่าน เลขบัตรเครดิต และข้อมูลส่วนบุคคลแบบเรียลไทม์ (Man-in-the-Middle Attack)",
        "remediation_th": "ตั้งค่าบน Nginx/Apache ให้ทำ 301 Permanent Redirect จาก HTTP พอร์ต 80 ไปยัง HTTPS พอร์ต 443",
    },
    "ncsa-02": {
        "why_th": "หากไม่มี HSTS แฮกเกอร์สามารถทำ SSL Stripping Attack โดยบังคับให้เบราว์เซอร์กลับไปใช้ HTTP แทน HTTPS ทำให้ดักจับข้อมูลได้แม้เซิร์ฟเวอร์จะรองรับ HTTPS แล้วก็ตาม",
        "remediation_th": "เพิ่ม HTTP Header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
    },
    "ncsa-03": {
        "why_th": "หากไม่ป้องกัน Clickjacking แฮกเกอร์สามารถสร้างหน้าเว็บปลอมที่ซ้อน iframe ของเว็บเป้าหมายไว้ด้านบน หลอกให้ผู้ใช้คลิกปุ่มที่มองไม่เห็น เช่น กดโอนเงิน กดอนุมัติคำสั่ง หรือเปลี่ยนรหัสผ่านโดยไม่รู้ตัว",
        "remediation_th": "ตั้งค่า Header: X-Frame-Options: SAMEORIGIN หรือใช้ Content-Security-Policy: frame-ancestors 'self'",
    },
    "ncsa-04": {
        "why_th": "หากเซิร์ฟเวอร์เปิดเผยยี่ห้อและเวอร์ชัน (เช่น Apache/2.4.49 หรือ PHP/7.4.3) แฮกเกอร์จะค้นหาช่องโหว่ CVE ที่ตรงกับเวอร์ชันนั้นได้ทันที และใช้ Exploit สำเร็จรูปเจาะระบบได้ภายในไม่กี่นาที",
        "remediation_th": "ตั้งค่าบน Nginx: server_tokens off; หรือบน Apache: ServerTokens Prod และ ServerSignature Off",
    },
    "ncsa-05": {
        "why_th": "หากใช้ TLS เวอร์ชันเก่า (TLS 1.0/1.1 หรือ SSLv3) แฮกเกอร์สามารถถอดรหัสข้อมูลที่เข้ารหัสได้ด้วยช่องโหว่ POODLE, BEAST, CRIME ทำให้ข้อมูลที่คิดว่าเข้ารหัสแล้วถูกอ่านได้ทั้งหมด",
        "remediation_th": "ตั้งค่าบน Web Server: ssl_protocols TLSv1.2 TLSv1.3; (ปิดการใช้งานเวอร์ชันเก่าทั้งหมด)",
    },
    "ncsa-06": {
        "why_th": "หากใช้ Cipher Suite ที่อ่อนแอ (เช่น RC4, DES, 3DES) แฮกเกอร์สามารถถอดรหัสข้อมูลที่ดักจับไว้ได้ด้วยเทคนิค Brute Force หรือช่องโหว่เฉพาะของ Cipher นั้น ข้อมูลผู้ใช้ทั้งหมดเสี่ยงถูกเปิดเผย",
        "remediation_th": "ใช้ชุดรหัสมาตรฐานสมัยใหม่ เช่น ECDHE-ECDSA-AES128-GCM-SHA256, ECDHE-RSA-AES128-GCM-SHA256 ปิด RC4/3DES/DES",
    },
    "ncsa-07": {
        "why_th": "หากมีช่องโหว่ XSS แฮกเกอร์สามารถฝังโค้ด JavaScript อันตรายลงในหน้าเว็บ เพื่อขโมย Cookies, Session Token และข้อมูลส่วนบุคคลของผู้ใช้ หรือเปลี่ยนเส้นทางไปยังเว็บฟิชชิ่ง หากมีช่องโหว่ SQL Injection แฮกเกอร์สามารถอ่าน แก้ไข หรือลบข้อมูลในฐานข้อมูลทั้งหมดได้",
        "remediation_th": "ใช้ Parameterized Queries (Prepared Statements), ทำ Input Sanitization/Validation และติดตั้ง WAF",
    },
    "ncsa-08": {
        "why_th": "หาก Cookie ไม่มี Secure Flag แฮกเกอร์ดักจับ Cookie ผ่าน HTTP ได้ หากไม่มี HttpOnly แฮกเกอร์ขโมย Cookie ด้วย XSS (document.cookie) หากไม่มี SameSite แฮกเกอร์ทำ CSRF Attack ส่งคำสั่งแทนผู้ใช้ได้ เช่น โอนเงิน เปลี่ยนรหัสผ่าน",
        "remediation_th": "ตั้งค่า Cookie ให้มี Flags ครบ: Set-Cookie: sessionId=...; Secure; HttpOnly; SameSite=Lax",
    },
    "ncsa-09": {
        "why_th": "หากเปิดเผยชื่อและเวอร์ชัน Framework (เช่น WordPress 5.8, jQuery 3.3.1) แฮกเกอร์จะค้นหาช่องโหว่ที่รู้จัก (Known Exploits) ของเวอร์ชันนั้นได้ทันที และโจมตีแบบอัตโนมัติด้วยเครื่องมือสำเร็จรูป",
        "remediation_th": "ลบ Header X-Powered-By และ meta generator tags ใน HTML (เช่น <meta name=\"generator\" ...>)",
    },
    "ncsa-10": {
        "why_th": "หากซอฟต์แวร์มีช่องโหว่ CVE ที่ยังไม่ได้แพตช์ แฮกเกอร์สามารถใช้ Exploit สำเร็จรูปจาก Metasploit หรือ Exploit-DB เจาะระบบได้ทันที โดยไม่ต้องมีความรู้ขั้นสูง มีความเสี่ยงสูงมากต่อการถูกยึดเซิร์ฟเวอร์",
        "remediation_th": "ตรวจสอบและอัปเดตเวอร์ชันของ CMS, ปลั๊กอิน, ไลบรารี และระบบปฏิบัติการให้เป็นเวอร์ชันล่าสุดที่มี Security Patch",
    },
    "ncsa-11": {
        "why_th": "หากหน้า /admin, /wp-admin, /login เปิดให้เข้าถึงจากอินเทอร์เน็ต แฮกเกอร์จะใช้เครื่องมือ Brute Force เดารหัสผ่านอัตโนมัติ (เช่น Hydra, Burp Suite) ทดลองรหัสผ่านหลายแสนชุด หากเจาะสำเร็จจะควบคุมระบบได้ทั้งหมด",
        "remediation_th": "จำกัดการเข้าถึงหน้าจัดการด้วย IP Whitelist, กำหนดให้เข้าผ่าน VPN ภายในองค์กร และเปิดใช้ 2FA",
    },

    # ═════════════════════════════════════════════════════════════════
    #  4. OWASP HTTP Security Headers (11 items)
    # ═════════════════════════════════════════════════════════════════
    "owasp-01": {
        "why_th": "หากไม่มี Content-Security-Policy (CSP) แฮกเกอร์สามารถโจมตีด้วย XSS โดยฝังโค้ด JavaScript อันตรายลงในหน้าเว็บ เพื่อขโมย Cookies, Session Token หรือข้อมูลส่วนบุคคลของผู้ใช้งาน หรือเปลี่ยนเส้นทางไปยังเว็บไซต์ฟิชชิ่ง",
        "remediation_th": "เพิ่ม Header: Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; script-src 'self'; style-src 'self' 'unsafe-inline';",
    },
    "owasp-02": {
        "why_th": "หากไม่มี HSTS แฮกเกอร์สามารถทำ Man-in-the-Middle Attack ดักจับการเชื่อมต่อและบังคับให้ Downgrade จาก HTTPS เป็น HTTP (SSL Stripping) ทำให้ข้อมูลที่ส่งถูกดักอ่านได้ทั้งหมด รวมถึงรหัสผ่านและข้อมูลบัตรเครดิต",
        "remediation_th": "เพิ่ม Header: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload",
    },
    "owasp-03": {
        "why_th": "หากไม่มี X-Frame-Options แฮกเกอร์สามารถฝังหน้าเว็บของคุณใน iframe บนเว็บปลอม แล้วหลอกให้ผู้ใช้คลิกปุ่มที่ซ่อนอยู่ (Clickjacking) เช่น กดโอนเงิน กดอนุมัติธุรกรรม หรือเปลี่ยนการตั้งค่าบัญชีโดยไม่รู้ตัว",
        "remediation_th": "เพิ่ม Header: X-Frame-Options: SAMEORIGIN (หรือ DENY หากไม่ต้องการให้ฝังใน frame ใดๆ)",
    },
    "owasp-04": {
        "why_th": "หากไม่มี X-Content-Type-Options: nosniff เบราว์เซอร์จะเดาชนิดไฟล์เอง (MIME Sniffing) แฮกเกอร์สามารถอัปโหลดไฟล์ .txt ที่มีโค้ด JavaScript ซ่อนอยู่ เบราว์เซอร์จะรันเป็นสคริปต์แทนการแสดงเป็นข้อความ ทำให้เกิด XSS",
        "remediation_th": "เพิ่ม Header: X-Content-Type-Options: nosniff",
    },
    "owasp-05": {
        "why_th": "หากไม่มี Referrer-Policy เมื่อผู้ใช้คลิกลิงก์ไปยังเว็บภายนอก URL เต็มรวมถึง Query String จะถูกส่งไปด้วย หาก URL มีข้อมูลลับ เช่น Token, Session ID หรือข้อมูลค้นหาส่วนตัว เว็บภายนอกจะเห็นข้อมูลเหล่านั้นทั้งหมด",
        "remediation_th": "เพิ่ม Header: Referrer-Policy: strict-origin-when-cross-origin",
    },
    "owasp-06": {
        "why_th": "หากไม่มี Permissions-Policy เว็บไซต์ (รวมถึงโค้ดจาก Third-party/โฆษณา) สามารถเข้าถึงกล้อง ไมโครโฟน ตำแหน่ง GPS และระบบชำระเงินของผู้ใช้ได้โดยไม่จำกัด สคริปต์โฆษณาที่ถูกแฮกอาจแอบเปิดกล้องหรือติดตามตำแหน่ง",
        "remediation_th": "เพิ่ม Header: Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()",
    },
    "owasp-07": {
        "why_th": "หากไม่มี COOP (Cross-Origin-Opener-Policy) หน้าเว็บที่เปิดจาก window.open สามารถเข้าถึง window.opener ได้ แฮกเกอร์ใช้ช่องโหว่ Spectre อ่านข้อมูลจากหน่วยความจำ หรือเปลี่ยนเส้นทางหน้าต้นทางไปยังเว็บฟิชชิ่ง",
        "remediation_th": "เพิ่ม Header: Cross-Origin-Opener-Policy: same-origin",
    },
    "owasp-08": {
        "why_th": "หากไม่มี COEP (Cross-Origin-Embedder-Policy) เว็บจะโหลดทรัพยากรจากภายนอกโดยไม่ตรวจสอบสิทธิ์ แฮกเกอร์สามารถใช้ช่องโหว่ Spectre/Meltdown อ่านข้อมูลข้ามโดเมนจากหน่วยความจำของเบราว์เซอร์ได้",
        "remediation_th": "เพิ่ม Header: Cross-Origin-Embedder-Policy: require-corp (หรือ credentialless)",
    },
    "owasp-09": {
        "why_th": "หากไม่มี CORP (Cross-Origin-Resource-Policy) เว็บไซต์อื่นสามารถดึงรูปภาพ สคริปต์ API Response ของคุณไปใช้งาน ผู้โจมตีอาจดึงข้อมูลส่วนบุคคลของผู้ใช้ผ่านรูปภาพที่มีข้อมูลฝัง หรือ Hotlink ทรัพยากรทำให้เสียค่า Bandwidth",
        "remediation_th": "เพิ่ม Header: Cross-Origin-Resource-Policy: same-origin (หรือ same-site)",
    },
    "owasp-10": {
        "why_th": "หากไม่มี Cache-Control ที่เหมาะสม เบราว์เซอร์จะแคชหน้าเว็บที่มีข้อมูลส่วนบุคคลไว้ในเครื่อง ผู้ใช้รายถัดไปที่ใช้คอมพิวเตอร์สาธารณะ (ห้องสมุด ร้านเน็ต) สามารถกดปุ่ม Back เพื่อดูข้อมูลของผู้ใช้คนก่อนได้ทั้งหมด",
        "remediation_th": "สำหรับหน้าที่มีข้อมูลสำคัญ ให้เพิ่ม Header: Cache-Control: no-store, max-age=0, must-revalidate",
    },
    "owasp-11": {
        "why_th": "หาก Cookie ไม่มี Secure แฮกเกอร์ดักจับ Session ผ่าน HTTP ได้ หากไม่มี HttpOnly สคริปต์ XSS ขโมย Cookie ด้วย document.cookie ได้ หากไม่มี SameSite แฮกเกอร์ส่งคำสั่ง CSRF แทนผู้ใช้ เช่น โอนเงิน เปลี่ยนอีเมล ลบบัญชี",
        "remediation_th": "กำหนดค่า Cookie ทุกตัวด้วย: Set-Cookie: name=value; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400",
    },
}


def get_guidance(check_id: str) -> dict[str, str]:
    """Return guidance dict for given check_id or defaults."""
    return GUIDANCE.get(check_id, {
        "why_th": "ตรวจสอบความสอดคล้องตามมาตรฐานความปลอดภัยและการใช้งานสากล",
        "remediation_th": "ปรับปรุงโค้ดและโครงสร้างของเว็บไซต์ให้ถูกต้องตามข้อกำหนดมาตรฐาน",
    })
