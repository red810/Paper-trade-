import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --------------------------------------------------------------------------
# Set DATABASE_URL in your .env file.
#
# For LOCAL TESTING (no Supabase needed):
#   DATABASE_URL=sqlite:///./papertrade.db
#
# For SUPABASE (once you're ready):
#   DATABASE_URL=postgresql://postgres.xxxx:[YOUR-PASSWORD]@aws-0-xx.pooler.supabase.com:6543/postgres
# --------------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./papertrade.db")

# SQLite needs this extra arg; Postgres doesn't.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that provides a DB session per request and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()