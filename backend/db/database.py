"""
Database engine, session factory, and startup helpers.
"""
import os
import time
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from db.models import Base

logger = logging.getLogger("webscan.db")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:devpass@db:5432/potato_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables defined in models (idempotent)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(max_retries=30, delay=2):
    """Block until Postgres is accepting connections."""
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return True
        except OperationalError:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                "Database not ready (attempt %d/%d), retrying in %ds...",
                attempt + 1, max_retries, delay,
            )
            time.sleep(delay)
    return False


if __name__ == "__main__":
    init_db()
    print("Tables created successfully!")
