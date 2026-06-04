from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

# Use Turso (hosted libSQL) when configured, otherwise fall back to a local
# SQLite file for development. Turso speaks SQLite, so models are unchanged.
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")  # e.g. libsql://my-db-org.turso.io
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

if TURSO_DATABASE_URL:
    host = TURSO_DATABASE_URL.replace("libsql://", "").replace("https://", "").rstrip("/")
    DATABASE_URL = f"sqlite+libsql://{host}?authToken={TURSO_AUTH_TOKEN}&secure=true"
    connect_args = {}
else:
    DB_PATH = os.environ.get("DB_PATH", "badminton.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
