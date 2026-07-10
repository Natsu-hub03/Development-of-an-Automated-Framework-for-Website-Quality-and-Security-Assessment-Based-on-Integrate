from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, nullable=False)
    tool_name = Column(String, nullable=False)  # เช่น "wappalyzer"
    raw_data = Column(JSON, nullable=False)      # เก็บผลลัพธ์ดิบทั้งหมด
    created_at = Column(DateTime, default=datetime.utcnow)