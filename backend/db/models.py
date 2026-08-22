"""
SQLAlchemy ORM models for scan persistence.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    status = Column(String, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    results = relationship(
        "ScanResult", back_populates="scan", cascade="all, delete-orphan"
    )
    ai_reports = relationship(
        "AIReport", back_populates="scan", cascade="all, delete-orphan"
    )


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(
        Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    tool_name = Column(String, nullable=False)
    raw_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="results")


class AIReport(Base):
    """Persisted AI analysis — avoids re-running Ollama for same scan."""
    __tablename__ = "ai_reports"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(
        Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String, nullable=False, index=True)
    model_name = Column(String, nullable=False)
    analysis_text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="ai_reports")
