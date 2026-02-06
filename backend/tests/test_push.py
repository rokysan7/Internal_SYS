"""
Web Push 구독 API + send_push_to_user 유틸리티 테스트.
"""

from unittest.mock import MagicMock, patch

import pytest

from models import PushSubscription


# --------------- API Tests ---------------


SUBSCRIBE_PAYLOAD = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-123",
    "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUlsvzpD6Rgmj7qLz",
    "auth": "tBHItJI5svbpC7HmqnEeSQ",
}


def test_subscribe_creates_subscription(client, test_user, db_session):
    """POST /push/subscribe — 정상 구독 등록."""
    resp = client.post("/push/subscribe", json=SUBSCRIBE_PAYLOAD)
    assert resp.status_code == 201
    assert resp.json()["message"] == "Subscription created"

    sub = db_session.query(PushSubscription).filter_by(user_id=test_user.id).first()
    assert sub is not None
    assert sub.endpoint == SUBSCRIBE_PAYLOAD["endpoint"]
    assert sub.p256dh == SUBSCRIBE_PAYLOAD["p256dh"]
    assert sub.auth == SUBSCRIBE_PAYLOAD["auth"]


def test_subscribe_updates_existing(client, test_user, db_session):
    """POST /push/subscribe — 동일 endpoint 재등록 시 키 갱신."""
    client.post("/push/subscribe", json=SUBSCRIBE_PAYLOAD)

    updated = {**SUBSCRIBE_PAYLOAD, "p256dh": "UPDATED_KEY", "auth": "UPDATED_AUTH"}
    resp = client.post("/push/subscribe", json=updated)
    assert resp.status_code == 201
    assert resp.json()["message"] == "Subscription updated"

    subs = db_session.query(PushSubscription).filter_by(user_id=test_user.id).all()
    assert len(subs) == 1
    assert subs[0].p256dh == "UPDATED_KEY"


def test_unsubscribe_removes_subscription(client, test_user, db_session):
    """DELETE /push/unsubscribe — 정상 구독 해제."""
    client.post("/push/subscribe", json=SUBSCRIBE_PAYLOAD)

    resp = client.request(
        "DELETE", "/push/unsubscribe",
        json={"endpoint": SUBSCRIBE_PAYLOAD["endpoint"]},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Subscription removed"

    sub = db_session.query(PushSubscription).filter_by(user_id=test_user.id).first()
    assert sub is None


def test_unsubscribe_not_found(client):
    """DELETE /push/unsubscribe — 존재하지 않는 구독."""
    resp = client.request(
        "DELETE", "/push/unsubscribe",
        json={"endpoint": "https://nonexistent.example.com/push"},
    )
    assert resp.status_code == 404


def test_get_vapid_public_key(client):
    """GET /push/vapid-public-key — VAPID 공개키 반환."""
    with patch("routers.push.VAPID_PUBLIC_KEY", "test-vapid-key-123"):
        resp = client.get("/push/vapid-public-key")
    assert resp.status_code == 200
    assert resp.json()["public_key"] == "test-vapid-key-123"


def test_get_vapid_public_key_not_configured(client):
    """GET /push/vapid-public-key — 미설정 시 500."""
    with patch("routers.push.VAPID_PUBLIC_KEY", ""):
        resp = client.get("/push/vapid-public-key")
    assert resp.status_code == 500


# --------------- send_push_to_user Unit Tests ---------------


def _create_subscription(db_session, user_id, endpoint="https://push.example.com/sub1"):
    """헬퍼: PushSubscription 레코드 생성."""
    sub = PushSubscription(
        user_id=user_id,
        endpoint=endpoint,
        p256dh="test_p256dh",
        auth="test_auth",
    )
    db_session.add(sub)
    db_session.commit()
    return sub


@patch("services.push.VAPID_PRIVATE_KEY", "fake-private-key")
@patch("services.push.VAPID_CLAIMS_EMAIL", "mailto:test@example.com")
@patch("services.push.webpush")
def test_send_push_success(mock_webpush, db_session, test_user):
    """send_push_to_user — 정상 전송."""
    from services.push import send_push_to_user

    _create_subscription(db_session, test_user.id)
    _create_subscription(db_session, test_user.id, "https://push.example.com/sub2")

    sent = send_push_to_user(db_session, test_user.id, "Title", "Body", 42)
    assert sent == 2
    assert mock_webpush.call_count == 2


@patch("services.push.VAPID_PRIVATE_KEY", "fake-private-key")
@patch("services.push.VAPID_CLAIMS_EMAIL", "mailto:test@example.com")
@patch("services.push.webpush")
def test_send_push_expired_cleanup(mock_webpush, db_session, test_user):
    """send_push_to_user — 410 응답 시 만료 구독 자동 삭제."""
    from pywebpush import WebPushException
    from services.push import send_push_to_user

    _create_subscription(db_session, test_user.id)

    mock_response = MagicMock()
    mock_response.status_code = 410
    mock_webpush.side_effect = WebPushException("Gone", response=mock_response)

    sent = send_push_to_user(db_session, test_user.id, "Title", "Body", 1)
    assert sent == 0

    remaining = db_session.query(PushSubscription).filter_by(user_id=test_user.id).all()
    assert len(remaining) == 0


@patch("services.push.VAPID_PRIVATE_KEY", "")
def test_send_push_skips_without_vapid(db_session, test_user):
    """send_push_to_user — VAPID 미설정 시 0 반환."""
    from services.push import send_push_to_user

    _create_subscription(db_session, test_user.id)
    sent = send_push_to_user(db_session, test_user.id, "Title", "Body")
    assert sent == 0


def test_send_push_no_subscriptions(db_session, test_user):
    """send_push_to_user — 구독 없으면 0 반환."""
    from services.push import send_push_to_user

    with patch("services.push.VAPID_PRIVATE_KEY", "key"), \
         patch("services.push.VAPID_CLAIMS_EMAIL", "mailto:t@t.com"):
        sent = send_push_to_user(db_session, test_user.id, "Title", "Body")
    assert sent == 0
