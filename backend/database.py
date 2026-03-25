import os
import pathlib

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Allow DATABASE_URL to be overridden by environment variable (e.g. on Railway with a volume)
_default_db_path = pathlib.Path(__file__).resolve().parent / "hawkear.db"
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{_default_db_path}"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
