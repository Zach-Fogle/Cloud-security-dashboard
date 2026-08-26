import os
os.environ["DATABASE_URL"] = "sqlite://"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def override():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def finding_payload():
    return {"source":"manual","source_finding_id":"M-1","title":"Public database","description":"Database is public","severity":"critical","status":"open","cloud_provider":"aws","account_id":"123","resource_type":"RDS","resource_id":"db-1","application":"Billing","owner":"Platform","environment":"production","first_detected_at":"2026-01-01T00:00:00Z","due_date":"2026-01-10","remediation_guidance":"Make it private"}
