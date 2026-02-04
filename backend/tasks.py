"""
Celery 비동기 태스크.
- check_pending_cases: 24시간 미처리 CS 리마인드 알림
- notify_comment: 댓글 등록 시 담당자 알림
- notify_case_assigned: 케이스 배정 시 담당자 알림
- notify_reply: 답글 등록 시 부모 댓글 작성자 알림
"""

from datetime import datetime, timedelta

from celery_app import celery
from database import SessionLocal
from models import CaseStatus, CSCase, Notification, NotificationType


@celery.task
def check_pending_cases():
    """24시간 이상 미처리 상태인 CS Case의 담당자에게 리마인드 알림을 생성한다."""
    db = SessionLocal()
    try:
        threshold = datetime.utcnow() - timedelta(hours=24)
        pending_cases = (
            db.query(CSCase)
            .filter(CSCase.status != CaseStatus.DONE, CSCase.created_at <= threshold)
            .all()
        )

        created = 0
        for case in pending_cases:
            if not case.assignees:
                continue

            # 이미 동일 리마인드가 최근 24시간 내에 존재하면 중복 생성 방지
            existing = (
                db.query(Notification)
                .filter(
                    Notification.case_id == case.id,
                    Notification.type == NotificationType.REMINDER,
                    Notification.created_at >= threshold,
                )
                .first()
            )
            if existing:
                continue

            for assignee in case.assignees:
                notif = Notification(
                    user_id=assignee.id,
                    case_id=case.id,
                    message=f"CS Case #{case.id} 미처리 24시간 경과: {case.title[:50]}",
                    type=NotificationType.REMINDER,
                )
                db.add(notif)
                created += 1

        db.commit()
        return {"checked": len(pending_cases), "notifications_created": created}
    finally:
        db.close()


@celery.task
def notify_comment(case_id: int, comment_author_id: int, comment_content: str):
    """댓글 작성 시 담당자에게 비동기 알림을 생성한다."""
    db = SessionLocal()
    try:
        case = db.query(CSCase).filter(CSCase.id == case_id).first()
        if not case or not case.assignees:
            return {"notified": False, "reason": "no case or no assignee"}

        notified_ids = []
        for assignee in case.assignees:
            if assignee.id == comment_author_id:
                continue
            notif = Notification(
                user_id=assignee.id,
                case_id=case.id,
                message=f"CS Case #{case.id}에 새로운 댓글: {comment_content[:50]}",
                type=NotificationType.COMMENT,
            )
            db.add(notif)
            notified_ids.append(assignee.id)

        db.commit()
        if not notified_ids:
            return {"notified": False, "reason": "author is only assignee"}
        return {"notified": True, "notified_user_ids": notified_ids}
    finally:
        db.close()


@celery.task
def notify_case_assigned(case_id: int, assignee_ids: list):
    """케이스 배정 시 담당자에게 비동기 알림을 생성한다."""
    db = SessionLocal()
    try:
        case = db.query(CSCase).filter(CSCase.id == case_id).first()
        if not case or not assignee_ids:
            return {"notified": False, "reason": "no case or no assignees"}

        for uid in assignee_ids:
            notif = Notification(
                user_id=uid,
                case_id=case.id,
                message=f"CS Case #{case.id} '{case.title[:50]}' 담당으로 배정되었습니다.",
                type=NotificationType.ASSIGNEE,
            )
            db.add(notif)

        db.commit()
        return {"notified": True, "notified_user_ids": assignee_ids}
    finally:
        db.close()


@celery.task
def notify_reply(case_id: int, parent_author_id: int, replier_name: str, replier_id: int):
    """답글 작성 시 부모 댓글 작성자에게 비동기 알림을 생성한다."""
    db = SessionLocal()
    try:
        if parent_author_id == replier_id:
            return {"notified": False, "reason": "self-reply"}

        notif = Notification(
            user_id=parent_author_id,
            case_id=case_id,
            message=f"{replier_name}님이 회원님의 댓글에 답글을 남겼습니다.",
            type=NotificationType.COMMENT,
        )
        db.add(notif)
        db.commit()
        return {"notified": True, "notified_user_id": parent_author_id}
    finally:
        db.close()
