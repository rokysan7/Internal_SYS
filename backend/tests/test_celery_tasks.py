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


def _make_case(db, assignees=None, status=CaseStatus.OPEN, created_at=None):
    """케이스 생성. assignees: User 객체 리스트 (many-to-many 관계 설정)."""
    case = CSCase(
        title="Test Case",
        content="Content",
        requester="Cust",
        assignee_id=assignees[0].id if assignees else None,
        status=status,
    )
    db.add(case)
    db.flush()
    if assignees:
        case.assignees = assignees
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
    case = _make_case(db_session, assignees=[user], created_at=old_time)

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
        db_session, assignees=[user],
        status=CaseStatus.DONE, created_at=old_time,
    )

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] == 0


def test_check_pending_skips_no_assignee(db_session):
    old_time = datetime.utcnow() - timedelta(hours=25)
    _make_case(db_session, assignees=None, created_at=old_time)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] == 0


def test_check_pending_skips_recent(db_session):
    user = _make_user(db_session)
    # 1시간 전 생성 (24시간 미만)
    recent_time = datetime.utcnow() - timedelta(hours=1)
    _make_case(db_session, assignees=[user], created_at=recent_time)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import check_pending_cases
            result = check_pending_cases()

    assert result["notifications_created"] == 0


def test_check_pending_dedup(db_session):
    """이미 24시간 내 REMINDER가 있으면 중복 생성 안함."""
    user = _make_user(db_session)
    old_time = datetime.utcnow() - timedelta(hours=25)
    case = _make_case(db_session, assignees=[user], created_at=old_time)

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
    case = _make_case(db_session, assignees=[assignee])

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
    case = _make_case(db_session, assignees=None)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_comment
            result = notify_comment(case.id, 1, "Comment")

    assert result["notified"] is False


def test_notify_comment_skips_self(db_session):
    user = _make_user(db_session)
    case = _make_case(db_session, assignees=[user])

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_comment
            result = notify_comment(case.id, user.id, "My own comment")

    assert result["notified"] is False


# ========== notify_reply ==========


def test_notify_reply_creates_notification(db_session):
    parent_author = _make_user(db_session, name="Parent", email="p@t.com")
    replier = _make_user(db_session, name="Replier", email="r@t.com")
    case = _make_case(db_session, assignees=[parent_author])

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_reply
            result = notify_reply(case.id, parent_author.id, replier.name, replier.id)

    assert result["notified"] is True
    notif = db_session.query(Notification).filter(
        Notification.case_id == case.id,
        Notification.type == NotificationType.COMMENT,
        Notification.user_id == parent_author.id,
    ).first()
    assert notif is not None


def test_notify_reply_skips_self(db_session):
    user = _make_user(db_session)
    case = _make_case(db_session, assignees=[user])

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import notify_reply
            result = notify_reply(case.id, user.id, user.name, user.id)

    assert result["notified"] is False


# ========== learn_tags_from_case ==========


def test_learn_tags_from_case_task(db_session):
    """learn_tags_from_case updates TagMaster keyword_weights."""
    from models import TagMaster

    case = CSCase(
        title="결제 오류 문의",
        content="신용카드 결제가 안됩니다",
        requester="Cust",
        tags=["결제테스트"],
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import learn_tags_from_case
            result = learn_tags_from_case(case.id)

    assert result["learned"] is True
    tag = db_session.query(TagMaster).filter(TagMaster.name == "결제테스트").first()
    assert tag is not None
    assert tag.usage_count >= 1
    assert len(tag.keyword_weights) > 0


# ========== compute_case_similarity ==========


def test_compute_case_similarity_task(db_session):
    """compute_case_similarity creates Redis cache entries."""
    _cache = {}

    def _fake_set(key, value, ex=None):
        _cache[key] = value

    def _fake_get(key):
        return _cache.get(key)

    def _fake_delete(key):
        _cache.pop(key, None)

    case1 = CSCase(
        title="결제 오류 발생", content="카드 결제 안됨",
        requester="A", tags=["결제"],
    )
    case2 = CSCase(
        title="결제 취소 문의", content="결제 취소하고 싶습니다",
        requester="B", tags=["결제"],
    )
    db_session.add_all([case1, case2])
    db_session.commit()
    db_session.refresh(case1)
    db_session.refresh(case2)

    with patch("tasks.SessionLocal", return_value=db_session), \
         patch.object(db_session, "close"), \
         patch("services.cache.cache_redis") as mock_redis:
        mock_redis.set = _fake_set
        mock_redis.get = _fake_get
        mock_redis.delete = _fake_delete
        from tasks import compute_case_similarity
        result = compute_case_similarity(case1.id)

    assert result["case_id"] == case1.id


# ========== rebuild_tfidf_model ==========


def test_rebuild_tfidf_model_task(db_session):
    """rebuild_tfidf_model saves model to Redis and caches similarity."""
    _cache = {}

    def _fake_set(key, value, ex=None):
        _cache[key] = value

    def _fake_get(key):
        return _cache.get(key)

    def _fake_delete(key):
        _cache.pop(key, None)

    for i in range(3):
        case = CSCase(
            title=f"테스트 케이스 {i}", content=f"내용 {i}",
            requester="Cust", tags=["테스트"],
        )
        db_session.add(case)
    db_session.commit()

    with patch("tasks.SessionLocal", return_value=db_session), \
         patch.object(db_session, "close"), \
         patch("services.cache.cache_redis") as mock_redis:
        mock_redis.set = _fake_set
        mock_redis.get = _fake_get
        mock_redis.delete = _fake_delete
        from tasks import rebuild_tfidf_model
        result = rebuild_tfidf_model()

    assert result["model_saved"] is True
    assert result["cases_count"] == 3
    assert "tfidf_model" in _cache


# ========== cleanup_tag_keywords ==========


def test_cleanup_tag_keywords_task(db_session):
    """cleanup_tag_keywords removes low-frequency keywords and unused tags."""
    from models import TagMaster

    # Tag with low-frequency keywords
    tag1 = TagMaster(
        name="정리대상", usage_count=5, created_by="user",
        keyword_weights={"결제": 5, "임시": 1, "테스트": 1},
    )
    # Unused tag (not seed)
    tag2 = TagMaster(
        name="미사용태그", usage_count=0, created_by="user",
        keyword_weights={},
    )
    # Unused seed tag (should be preserved)
    tag3 = TagMaster(
        name="시드태그", usage_count=0, created_by="seed",
        keyword_weights={},
    )
    db_session.add_all([tag1, tag2, tag3])
    db_session.commit()

    with patch("tasks.SessionLocal", return_value=db_session):
        with patch.object(db_session, "close"):
            from tasks import cleanup_tag_keywords
            result = cleanup_tag_keywords()

    assert result["removed_keywords"] == 2  # "임시", "테스트"
    assert result["removed_tags"] == 1  # "미사용태그"
    assert result["cleaned_tags"] == 1  # "정리대상"

    # Verify tag1 cleaned
    db_session.refresh(tag1)
    assert "임시" not in tag1.keyword_weights
    assert "결제" in tag1.keyword_weights

    # Verify tag2 deleted
    assert db_session.query(TagMaster).filter(TagMaster.name == "미사용태그").first() is None

    # Verify seed tag preserved
    assert db_session.query(TagMaster).filter(TagMaster.name == "시드태그").first() is not None
