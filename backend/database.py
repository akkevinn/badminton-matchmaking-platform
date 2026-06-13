from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

# Use Turso (hosted libSQL) when configured, otherwise fall back to a local
# SQLite file for development. Turso speaks SQLite, so models are unchanged.
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL")  # e.g. libsql://my-db-org.turso.io
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN")

if TURSO_DATABASE_URL:
    if not TURSO_AUTH_TOKEN:
        raise RuntimeError(
            "TURSO_DATABASE_URL is set but TURSO_AUTH_TOKEN is missing/empty. "
            "Set TURSO_AUTH_TOKEN in your host's environment variables (Production scope) "
            "and redeploy."
        )
    host = TURSO_DATABASE_URL.replace("libsql://", "").replace("https://", "").rstrip("/")
    # The auth token MUST go through connect_args (the dialect ignores an
    # authToken query param); `secure=true` selects the wss/https transport.
    DATABASE_URL = f"sqlite+libsql://{host}?secure=true"
    connect_args = {"auth_token": TURSO_AUTH_TOKEN}
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
    _run_migrations()


def _run_migrations():
    """Lightweight, idempotent column additions (create_all does not ALTER)."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if "tournaments" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("tournaments")}
    stmts = []
    if "sport" not in cols:
        stmts.append("ALTER TABLE tournaments ADD COLUMN sport VARCHAR DEFAULT 'badminton'")
    if "closed_courts" not in cols:
        stmts.append("ALTER TABLE tournaments ADD COLUMN closed_courts TEXT DEFAULT '[]'")
    if stmts:
        with engine.begin() as conn:
            for stmt in stmts:
                conn.execute(text(stmt))
