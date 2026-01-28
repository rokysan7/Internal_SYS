"""인증 API 테스트."""


def test_login_success(client, test_user):
    resp = client.post("/auth/login", json={
        "email": "author@test.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    resp = client.post("/auth/login", json={
        "email": "author@test.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_nonexistent_email(client):
    resp = client.post("/auth/login", json={
        "email": "nobody@test.com",
        "password": "testpass123",
    })
    assert resp.status_code == 401


def test_get_me_authenticated(client, test_user, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "author@test.com"
    assert data["name"] == "Test Author"


def test_get_me_no_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_get_me_invalid_token(client):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
