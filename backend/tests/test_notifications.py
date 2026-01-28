"""Notification API 테스트."""

from models import Notification, NotificationType


def test_list_notifications(client, sample_case, assignee_user):
    """sample_case 생성 시 ASSIGNEE 알림이 자동 생성됨."""
    resp = client.get("/notifications/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_list_notifications_filter_user(client, sample_case, assignee_user, test_user):
    resp = client.get("/notifications/", params={"user_id": assignee_user.id})
    assert resp.status_code == 200
    for n in resp.json():
        assert n["user_id"] == assignee_user.id

    # test_user에게는 알림 없음
    resp2 = client.get("/notifications/", params={"user_id": test_user.id})
    assert len(resp2.json()) == 0


def test_list_notifications_unread_only(client, sample_case, assignee_user):
    resp = client.get("/notifications/", params={"unread_only": True})
    assert resp.status_code == 200
    for n in resp.json():
        assert n["is_read"] is False


def test_mark_as_read(client, sample_case, assignee_user):
    notifs = client.get("/notifications/").json()
    assert len(notifs) > 0
    nid = notifs[0]["id"]

    resp = client.patch(f"/notifications/{nid}/read")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # 읽음 처리 확인
    updated = client.get("/notifications/", params={"unread_only": True}).json()
    assert all(n["id"] != nid for n in updated)


def test_mark_as_read_not_found(client):
    resp = client.patch("/notifications/99999/read")
    assert resp.status_code == 404


def test_notification_on_case_creation(client, test_user, assignee_user, sample_product):
    """케이스 생성 → 담당자 알림 → unread 카운트 확인."""
    client.post("/cases/", json={
        "title": "Badge Test",
        "content": "Content",
        "requester": "Cust",
        "assignee_id": assignee_user.id,
        "product_id": sample_product["id"],
    })
    unread = client.get(
        "/notifications/",
        params={"user_id": assignee_user.id, "unread_only": True},
    ).json()
    assert len(unread) == 1
    assert unread[0]["type"] == "ASSIGNEE"


def test_notification_badge_count(client, test_user, assignee_user, sample_product):
    """여러 케이스 생성 → unread 카운트 정확성."""
    for i in range(3):
        client.post("/cases/", json={
            "title": f"Case {i}",
            "content": "Content",
            "requester": "Cust",
            "assignee_id": assignee_user.id,
        })
    unread = client.get(
        "/notifications/",
        params={"user_id": assignee_user.id, "unread_only": True},
    ).json()
    assert len(unread) == 3
