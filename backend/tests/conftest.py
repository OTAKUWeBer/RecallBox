import sys
from pathlib import Path

# Ensure backend and project root directory are in sys.path
backend_dir = Path(__file__).resolve().parent.parent
project_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db, init_fts5_tables
from app.models.entities import Memory, Tag, Relationship, Reminder
from app.security.auth import get_or_create_auth_token
from fastapi.testclient import TestClient
from app.main import app

TEST_DB_PATH = "test_recallbox.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    # Init FTS5 for test db
    with test_engine.connect() as conn:
        conn.exec_driver_sql("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id UNINDEXED,
                title,
                content,
                summary,
                user_why,
                tags,
                source_url,
                tokenize = 'porter unicode61'
            );
        """)
        conn.commit()
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def auth_token():
    return get_or_create_auth_token()

@pytest.fixture
def auth_headers(auth_token):
    return {"X-RecallBox-Key": auth_token}

@pytest.fixture
def client(db_session, auth_token):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-RecallBox-Key": auth_token}) as c:
        yield c
    app.dependency_overrides.clear()
