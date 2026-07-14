FROM python:3.11-slim

# เพิ่มส่วนนี้เข้าไปเพื่อติดตั้ง Library ที่ Chrome/Puppeteer ต้องการ
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    wget \
    gnupg \
    ca-certificates \
    libgobject-2.0-0 \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/
COPY scanner/ /app/scanner/
RUN npm install --prefix /app/scanner

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
