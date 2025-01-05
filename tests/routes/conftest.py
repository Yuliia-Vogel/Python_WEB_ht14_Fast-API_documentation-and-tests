import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock, patch

from main import app as app_application
from src.database.models import Base
from src.database.db import get_db
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def session():
    # Create the database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client(session):
    # Dependency override
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app_application.dependency_overrides[get_db] = override_get_db

    yield TestClient(app_application)


@pytest.fixture(scope="module", autouse=True)
def disable_rate_limiter():
    with patch("fastapi_limiter.depends.RateLimiter.__call__", new_callable=AsyncMock) as mock_rate_limiter_call:
        mock_rate_limiter_call.return_value = None
        yield


@pytest.fixture(scope="module")
def user():
    return {"username": "deadpool", "email": "deadpool@example.com", "password": "123456789"}
