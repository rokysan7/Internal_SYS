"""Celery 태스크 직접 호출 테스트.
tasks.SessionLocal을 monkeypatch하여 테스트 DB 세션 사용.
"""

from datetime import datetime, timedelta
from unittest.mock import patch

from models import CaseStatus, CSCase, Notification, NotificationType, User, UserRole
from routers.auth import pwd_context


def _make_user(db, name="User", email="u@t.com", role=UserRole.CS):
    user = User(
        name=name, email=email,
        password_hash=pwd_context.hash("pass"),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_case(db, assignee_id=None, status=CaseStatus.OPEN, created_at=None):
    case = CSCase(
        title="Test Case",
        content="Content",
        requester="Cust",
        assignee_id=assignee_id,
        status=status,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    if created_at:
        db.execute(
            CSCase.__table__.update()
            .where(CSCase.__table__.c.id == case.id)
            .values(created_at=created_at)
        )
        db.commit()
        db.refresh(case)
    return case


# ========== check_pending_cases ==========


def test_check_pending_creates_reminder(db_session):
    user = _make_user(db_session)
    old_time = datetime.utcnow() - timedelta(hours=25)
    case = _make_case(db_session, assignee_id=user.id, created_at=old_time)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] >= 1
    notif = db_session.query(Notification).filter(
        Notification.case_id == case.id,
        Notification.type == NotificationType.REMINDER,
    ).first()
    assert notif is not None


def test_check_pending_skips_done(db_session):
    user = _make_user(db_session)
    old_time = datetime.utcnow() - timedelta(hours=25)
    _make_case(
        db_session, assignee_id=user.id,
        status=CaseStatus.DONE, created_at=old_time,
    )

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] == 0


def test_check_pending_skips_no_assignee(db_session):
    old_time = datetime.utcnow() - timedelta(hours=25)
    _make_case(db_session, assignee_id=None, created_at=old_time)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] == 0


def test_check_pending_skips_recent(db_session):
    user = _make_user(db_session)
    # 1시간 전 생성 (24시간 미만)
    recent_time = datetime.utcnow() - timedelta(hours=1)
    _make_case(db_session, assignee_id=user.id, created_at=recent_time)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] == 0


def test_check_pending_dedup(db_session):
    """이미 24시간 내 REMINDER가 있으면 중복 생성 안함."""
    user = _make_user(db_session)
    old_time = datetime.utcnow() - timedelta(hours=25)
    case = _make_case(db_session, assignee_id=user.id, created_at=old_time)

    # 기존 리마인더 생성
    existing = Notification(
        user_id=user.id,
        case_id=case.id,
        message="Existing reminder",
        type=NotificationType.REMINDER,
    )
    db_session.add(existing)
    db_session.commit()

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] == 0


# ========== notify_comment ==========


def test_notify_comment_creates_notification(db_session):
    assignee = _make_user(db_session, name="Assignee", email="a@t.com")
    author = _make_user(db_session, name="Author", email="b@t.com")
    case = _make_case(db_session, assignee_id=assignee.id)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_comment
            result = notify_comment(case.id, author.id, "Hello comment")

    assert result["notified"] is True
    notif = db_session.query(Notification).filter(
        Notification.case_id == case.id,
        Notification.type == NotificationType.COMMENT,
    ).first()
    assert notif is not None
    assert notif.user_id == assignee.id


def test_notify_comment_skips_no_case(db_session):
    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_comment
            result = notify_comment(99999, 1, "Comment")

    assert result["notified"] is False


def test_notify_comment_skips_no_assignee(db_session):
    _make_user(db_session)  # ensure user exists
    case = _make_case(db_session, assignee_id=None)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_comment
            result = notify_comment(case.id, 1, "Comment")

    assert result["notified"] is False


def test_notify_comment_skips_self(db_session):
    user = _make_user(db_session)
    case = _make_case(db_session, assignee_id=user.id)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_comment
            result = notify_comment(case.id, user.id, "My own comment")

    assert result["notified"] is False
