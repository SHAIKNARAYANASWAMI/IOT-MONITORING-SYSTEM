import os

# Must be set BEFORE the app is imported, so tests never touch the real iot.db.
os.environ["DATABASE_URL"] = "sqlite:///./test_iot.db"

import pytest

from backend.app.database.session import Base, SessionLocal, engine
from backend.app.models import models  # noqa: F401  (registers tables)

assert str(engine.url).endswith("test_iot.db"), "Tests must use the test database!"


@pytest.fixture(autouse=True)
def clean_db():
    """Fresh empty tables before every test, so tests never affect each other."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()