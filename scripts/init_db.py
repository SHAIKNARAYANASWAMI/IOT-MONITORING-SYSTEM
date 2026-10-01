from backend.app.database.session import Base, engine
from backend.app.models import models  # noqa: F401  (import registers the tables with Base)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created:")
    for table_name in Base.metadata.tables:
        print(" -", table_name)


if __name__ == "__main__":
    init_db()