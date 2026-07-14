import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:devpass@localhost:5432/potato_db")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def wait_for_db(max_retries=30, delay=2):
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except OperationalError:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
    return False


if __name__ == "__main__":
    init_db()
    print("สร้างตารางสำเร็จ!")