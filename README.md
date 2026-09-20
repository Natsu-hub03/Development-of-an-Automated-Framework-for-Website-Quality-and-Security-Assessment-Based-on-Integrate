# WebScan (Potato)

**ระบบประเมินมาตรฐานและความปลอดภัยของเว็บไซต์อัตโนมัติ**

> สแกนเว็บไซต์ตามมาตรฐานสากล 4 ด้าน (71 ข้อ)

---

## 1. การติดตั้งและเตรียมเครื่อง (Prerequisites)

สำหรับคนที่เพิ่งลง Windows ใหม่เลย ต้องโหลดและติดตั้งสิ่งเหล่านี้ตามลำดับ:

> **รันผ่าน Docker:** ลงแค่ 3 อย่าง → Git, Docker Desktop

## Download Git & Docker Desktop

- Link: [https://git-scm.com/install/windows] & [https://www.docker.com/products/docker-desktop/]
- Check: `git --version` & `docker --version` # ต้องขึ้น: git version 2.xx.x.windows & Docker version 27.x.x
- Docker Desktop ต้องเปิด **WSL 2** — ตอนติดตั้งจะถามให้เปิดอัตโนมัติ ถ้าไม่ได้เปิด ให้รัน:
  powershell หรือ CMD: `wsl --install`

## ตั้งค่า Environment & รันระบบ

## bash

1. copy .env.example .env # สร้างไฟล์ .env จากตัวอย่าง
2. docker compose up -d --build # รันทุก services

- Check: `docker compose ps` — ต้องเห็น 4 services สถานะ "Up": db, backend, frontend, zap

## เข้าใช้งาน

- Scanner UI (หน้าหลัก): http://localhost:3000
- Dashboard: http://localhost:3000/dashboard
- API Docs (Swagger): http://localhost:8000/docs

## ปิดระบบ

## bash

docker compose down # ปิดทุก services
docker compose down -v # ปิด + ลบข้อมูล DB ด้วย
