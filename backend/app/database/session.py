from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import get_settings

settings = get_settings()

# SQLite needs check_same_thread=False because the MQTT worker thread
# and the API threads will both use the database.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

# Each request/worker gets its own session (a short-lived conversation with the DB).
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# All ORM table classes will inherit from this Base.
Base = declarative_base()


def get_db():
    """Gives one DB session and always closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()