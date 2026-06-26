import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ORIGINS", "http://localhost")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from main import app
from database import get_session
from limiter import limiter

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def get_session_test():
    with Session(test_engine) as session:
        yield session
    session.close()

@pytest.fixture(autouse=True)
def fresh_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture(autouse=True)
def stub_email_task(monkeypatch):
    
    monkeypatch.setattr("email_utils.send_verification_email.delay", lambda *a, **k: None)

@pytest.fixture
def client():
    app.dependency_overrides[get_session] = get_session_test
    limiter.enabled = False
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def session():
    with Session(test_engine) as session:
        yield session
