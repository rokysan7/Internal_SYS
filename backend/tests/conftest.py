"""
공통 테스트 Fixture.
- PostgreSQL 테스트 DB 사용 (ARRAY 타입 호환)
- 테스트마다 테이블 truncate + 시퀀스 리셋으로 격리
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
from models import User, UserRole
from routers.auth import pwd_context, create_access_token

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://seokan@localhost:5432/cs_dashboard_test",
)

engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---- session-scoped: 테이블 생성/삭제 ----

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---- function-scoped: 테스트 간 격리 ----

@pytest.fixture(autouse=True)
def clean_tables():
    """각 테스트 후 전체 테이블 truncate + 시퀀스 리셋."""
    yield
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        for table in Base.metadata.sorted_tables:
            conn.execute(
                text(f"ALTER SEQUENCE IF EXISTS {table.name}_id_seq RESTART WITH 1")
            )
        conn.commit()


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    """TestClient — get_db를 테스트 세션으로 오버라이드."""
    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---- 사용자 Fixture ----

@pytest.fixture()
def test_user(db_session):
    """author_id=1 hardcode와 매칭되는 첫 번째 유저."""
    user = User(
        name="Test Author",
        email="author@test.com",
        password_hash=pwd_context.hash("testpass123"),
        role=UserRole.CS,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def assignee_user(db_session, test_user):
    """담당자 알림 테스트용 두 번째 유저 (id != 1)."""
    user = User(
        name="Test Assignee",
        email="assignee@test.com",
        password_hash=pwd_context.hash("testpass123"),
        role=UserRole.ENGINEER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ---- 샘플 데이터 Fixture ----

@pytest.fixture()
def sample_product(client, test_user):
    resp = client.post("/products/", json={"name": "Test Product", "description": "desc"})
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def sample_license(client, sample_product):
    resp = client.post("/licenses/", json={
        "name": "Test License",
        "product_id": sample_product["id"],
        "description": "license desc",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def sample_case(client, test_user, assignee_user, sample_product, sample_license):
    """assignee_user를 담당자로 지정한 케이스. 생성 시 ASSIGNEE 알림도 자동 생성됨."""
    resp = client.post("/cases/", json={
        "title": "Test Case Title",
        "content": "Test case content for integration",
        "product_id": sample_product["id"],
        "license_id": sample_license["id"],
        "requester": "Customer A",
        "assignee_id": assignee_user.id,
        "priority": "MEDIUM",
        "tags": ["test", "integration"],
    })
    assert resp.status_code == 201
    return resp.json()
