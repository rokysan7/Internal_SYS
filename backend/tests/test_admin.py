"""Admin router user management 테스트."""


def test_list_users(client, test_user):
    resp = client.get("/admin/users")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_list_users_search(client, test_user, assignee_user):
    resp = client.get("/admin/users", params={"search": "Assignee"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Test Assignee"


def test_list_users_filter_role(client, test_user, assignee_user):
    resp = client.get("/admin/users", params={"role": "ENGINEER"})
    assert resp.status_code == 200
    for u in resp.json()["items"]:
        assert u["role"] == "ENGINEER"


def test_create_user(client, test_user):
    resp = client.post("/admin/users", json={
        "name": "New User",
        "email": "new@test.com",
        "password": "Str0ngPass!",
        "role": "CS",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New User"
    assert data["email"] == "new@test.com"
    assert data["role"] == "CS"


def test_create_user_duplicate_email(client, test_user):
    resp = client.post("/admin/users", json={
        "name": "Dup",
        "email": "author@test.com",
        "password": "Str0ngPass!",
        "role": "CS",
    })
    assert resp.status_code == 400
    assert "Email" in resp.json()["detail"]


def test_get_user(client, test_user):
    resp = client.get(f"/admin/users/{test_user.id}")
    assert resp.status_code == 200
    assert resp.json()["email"] == "author@test.com"


def test_get_user_not_found(client, test_user):
    resp = client.get("/admin/users/99999")
    assert resp.status_code == 404


def test_update_user(client, test_user, assignee_user):
    resp = client.put(f"/admin/users/{assignee_user.id}", json={
        "name": "Updated Name",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_update_user_not_found(client, test_user):
    resp = client.put("/admin/users/99999", json={"name": "X"})
    assert resp.status_code == 404


def test_update_user_cannot_change_own_role(client, test_user):
    resp = client.put(f"/admin/users/{test_user.id}", json={
        "role": "CS",
    })
    assert resp.status_code == 400
    assert "own role" in resp.json()["detail"]


def test_update_user_duplicate_email(client, test_user, assignee_user):
    resp = client.put(f"/admin/users/{assignee_user.id}", json={
        "email": "author@test.com",
    })
    assert resp.status_code == 400
    assert "Email" in resp.json()["detail"]


def test_delete_user(client, test_user, assignee_user):
    resp = client.delete(f"/admin/users/{assignee_user.id}")
    assert resp.status_code == 204

    # 비활성화 확인
    user_resp = client.get(f"/admin/users/{assignee_user.id}")
    assert user_resp.json()["is_active"] is False


def test_delete_user_not_found(client, test_user):
    resp = client.delete("/admin/users/99999")
    assert resp.status_code == 404


def test_delete_user_cannot_self(client, test_user):
    resp = client.delete(f"/admin/users/{test_user.id}")
    assert resp.status_code == 400
    assert "own account" in resp.json()["detail"]


def test_reset_password(client, test_user, assignee_user):
    resp = client.post(
        f"/admin/users/{assignee_user.id}/reset-password",
        json={"new_password": "NewStr0ng!"},
    )
    assert resp.status_code == 204


def test_reset_password_not_found(client, test_user):
    resp = client.post(
        "/admin/users/99999/reset-password",
        json={"new_password": "NewStr0ng!"},
    )
    assert resp.status_code == 404


def test_create_user_weak_password(client, test_user):
    resp = client.post("/admin/users", json={
        "name": "Weak",
        "email": "weak@test.com",
        "password": "short",
        "role": "CS",
    })
    assert resp.status_code == 400
    assert "Password" in resp.json()["detail"]
