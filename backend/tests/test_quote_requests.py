"""
Quote Request API 테스트.
"""

import pytest
from unittest.mock import patch

from models import QuoteRequest, QuoteRequestStatus, User, UserRole
from routers.auth import pwd_context

TEST_API_KEY = "test-api-key-12345"

# ---- Fixtures ----

SAMPLE_COLLECT_DATA = {
    "date_time": "2026-02-05 10:20:53",
    "delivery_date": "260205",
    "email_id": "19c2b22cf0e0522c",
    "email": "test@example.com",
    "organization": "Test Org",
    "quote_request": "product A/pro/12months\nproduct B/basic/6months",
    "other_request": "",
    "failed_products": [
        {"user_input": "null / null / 12months / 1", "result": "No matching product"}
    ],
    "additional_request": "Rush order",
}


@pytest.fixture(autouse=True)
def mock_api_key():
    with patch("routers.quote_requests.QUOTE_API_KEY", TEST_API_KEY):
        yield


@pytest.fixture()
def api_key_headers():
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture()
def sample_qr(client, api_key_headers):
    """Create a sample quote request via collect endpoint."""
    resp = client.post("/quote-requests/collect", json=SAMPLE_COLLECT_DATA, headers=api_key_headers)
    assert resp.status_code == 201
    qr_id = resp.json()["id"]
    return qr_id


@pytest.fixture()
def cs_user(db_session):
    """Non-admin CS user."""
    user = User(
        name="CS Staff",
        email="cs@test.com",
        password_hash=pwd_context.hash("testpass123"),
        role=UserRole.CS,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ---- Collect Endpoint ----


class TestCollect:
    def test_collect_creates_request(self, client, api_key_headers):
        resp = client.post("/quote-requests/collect", json=SAMPLE_COLLECT_DATA, headers=api_key_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "created"
        assert data["id"] > 0

    def test_collect_missing_required(self, client, api_key_headers):
        bad_data = {"date_time": "2026-01-01 00:00:00"}
        resp = client.post("/quote-requests/collect", json=bad_data, headers=api_key_headers)
        assert resp.status_code == 422

    def test_collect_invalid_date_format(self, client, api_key_headers):
        bad_data = {**SAMPLE_COLLECT_DATA, "date_time": "not-a-date"}
        resp = client.post("/quote-requests/collect", json=bad_data, headers=api_key_headers)
        assert resp.status_code == 422

    def test_collect_invalid_api_key(self, client):
        resp = client.post(
            "/quote-requests/collect",
            json=SAMPLE_COLLECT_DATA,
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_collect_no_api_key(self, client):
        resp = client.post("/quote-requests/collect", json=SAMPLE_COLLECT_DATA)
        assert resp.status_code == 422  # Missing header

    def test_collect_auto_assigns_default_users(self, client, api_key_headers, db_session):
        """Users with is_quote_assignee=True are auto-assigned on collect."""
        user = User(
            name="QR Handler",
            email="qr_handler@test.com",
            password_hash=pwd_context.hash("testpass123"),
            role=UserRole.CS,
            is_quote_assignee=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        resp = client.post("/quote-requests/collect", json=SAMPLE_COLLECT_DATA, headers=api_key_headers)
        assert resp.status_code == 201
        qr_id = resp.json()["id"]

        # Verify auto-assigned
        detail = client.get(f"/quote-requests/{qr_id}")
        assert user.id in detail.json()["assignee_ids"]

    def test_collect_no_default_users(self, client, api_key_headers, db_session):
        """When no users have is_quote_assignee=True, assignees list is empty."""
        # Ensure no default assignees exist
        db_session.query(User).update({User.is_quote_assignee: False})
        db_session.commit()

        resp = client.post("/quote-requests/collect", json=SAMPLE_COLLECT_DATA, headers=api_key_headers)
        assert resp.status_code == 201
        qr_id = resp.json()["id"]

        detail = client.get(f"/quote-requests/{qr_id}")
        assert detail.json()["assignee_ids"] == []


# ---- List ----


class TestList:
    def test_list_quote_requests(self, client, sample_qr):
        resp = client.get("/quote-requests/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_status_filter(self, client, sample_qr):
        resp = client.get("/quote-requests/", params={"status": "OPEN"})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "OPEN"

    def test_list_search_filter(self, client, sample_qr):
        resp = client.get("/quote-requests/", params={"search": "Test Org"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_list_non_admin_sees_only_assigned(self, client, sample_qr, cs_user, db_session):
        """Non-admin without assignment sees nothing."""
        from routers.auth import get_current_user
        from main import app

        app.dependency_overrides[get_current_user] = lambda: cs_user
        resp = client.get("/quote-requests/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

        # Assign cs_user, then they should see it
        qr = db_session.query(QuoteRequest).filter(QuoteRequest.id == sample_qr).first()
        qr.assignees = [cs_user]
        db_session.commit()

        resp = client.get("/quote-requests/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


# ---- Detail ----


class TestDetail:
    def test_get_detail(self, client, sample_qr):
        resp = client.get(f"/quote-requests/{sample_qr}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == sample_qr
        assert data["organization"] == "Test Org"
        assert data["failed_products"] is not None
        assert len(data["failed_products"]) == 1

    def test_get_detail_not_found(self, client):
        resp = client.get("/quote-requests/99999")
        assert resp.status_code == 404


# ---- Status Update ----


class TestStatusUpdate:
    def test_update_status_done(self, client, sample_qr, test_user, db_session):
        # Assign test_user first (admin)
        qr = db_session.query(QuoteRequest).filter(QuoteRequest.id == sample_qr).first()
        qr.assignees = [test_user]
        db_session.commit()

        resp = client.patch(f"/quote-requests/{sample_qr}/status", json={"status": "DONE"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "DONE"
        assert resp.json()["completed_at"] is not None

    def test_update_status_reopen(self, client, sample_qr, test_user, db_session):
        qr = db_session.query(QuoteRequest).filter(QuoteRequest.id == sample_qr).first()
        qr.assignees = [test_user]
        db_session.commit()

        client.patch(f"/quote-requests/{sample_qr}/status", json={"status": "DONE"})
        resp = client.patch(f"/quote-requests/{sample_qr}/status", json={"status": "OPEN"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "OPEN"
        assert resp.json()["completed_at"] is None

    def test_update_status_permission_denied(self, client, sample_qr, cs_user):
        from routers.auth import get_current_user
        from main import app

        app.dependency_overrides[get_current_user] = lambda: cs_user
        resp = client.patch(f"/quote-requests/{sample_qr}/status", json={"status": "DONE"})
        assert resp.status_code == 403


# ---- Assignees ----


class TestAssignees:
    def test_set_assignees(self, client, sample_qr, assignee_user):
        resp = client.put(
            f"/quote-requests/{sample_qr}/assignees",
            json={"assignee_ids": [assignee_user.id]},
        )
        assert resp.status_code == 200
        assert assignee_user.id in resp.json()["assignee_ids"]

    def test_set_assignees_admin_only(self, client, sample_qr, cs_user, assignee_user):
        from routers.auth import get_current_user
        from main import app

        app.dependency_overrides[get_current_user] = lambda: cs_user
        resp = client.put(
            f"/quote-requests/{sample_qr}/assignees",
            json={"assignee_ids": [assignee_user.id]},
        )
        assert resp.status_code == 403


# ---- Delete ----


class TestDelete:
    def test_delete_admin(self, client, sample_qr):
        resp = client.delete(f"/quote-requests/{sample_qr}")
        assert resp.status_code == 204

    def test_delete_non_admin(self, client, sample_qr, cs_user):
        from routers.auth import get_current_user
        from main import app

        app.dependency_overrides[get_current_user] = lambda: cs_user
        resp = client.delete(f"/quote-requests/{sample_qr}")
        assert resp.status_code == 403


# ---- Comments ----


class TestComments:
    def test_comments_crud(self, client, sample_qr):
        # Create
        resp = client.post(
            f"/quote-requests/{sample_qr}/comments",
            json={"content": "Test comment"},
        )
        assert resp.status_code == 201
        comment_id = resp.json()["id"]

        # List
        resp = client.get(f"/quote-requests/{sample_qr}/comments")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # Delete
        resp = client.delete(f"/quote-requests/{sample_qr}/comments/{comment_id}")
        assert resp.status_code == 204

    def test_comments_nested(self, client, sample_qr):
        # Parent comment
        resp = client.post(
            f"/quote-requests/{sample_qr}/comments",
            json={"content": "Parent comment"},
        )
        parent_id = resp.json()["id"]

        # Reply
        resp = client.post(
            f"/quote-requests/{sample_qr}/comments",
            json={"content": "Reply", "parent_id": parent_id},
        )
        assert resp.status_code == 201
        assert resp.json()["parent_id"] == parent_id

        # List should show nested structure
        resp = client.get(f"/quote-requests/{sample_qr}/comments")
        assert resp.status_code == 200
        tree = resp.json()
        assert len(tree) == 1  # Only parent at top level
        assert len(tree[0]["replies"]) == 1

    def test_comments_delete_permission(self, client, sample_qr, cs_user):
        # Create comment as admin
        resp = client.post(
            f"/quote-requests/{sample_qr}/comments",
            json={"content": "Admin comment"},
        )
        comment_id = resp.json()["id"]

        # cs_user (non-author, non-admin) cannot delete
        from routers.auth import get_current_user
        from main import app

        app.dependency_overrides[get_current_user] = lambda: cs_user
        resp = client.delete(f"/quote-requests/{sample_qr}/comments/{comment_id}")
        assert resp.status_code == 403
