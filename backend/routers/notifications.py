"""
Notification API 라우터.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Notification, User, UserRole
from routers.auth import get_current_user
from schemas import NotificationRead

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationRead])
def list_notifications(
    user_id: Optional[int] = Query(None, description="사용자 ID 필터"),
    unread_only: bool = Query(False, description="미읽음만 조회"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for current user. Admin can filter by user_id."""
    target_id = user_id if (user_id and current_user.role == UserRole.ADMIN) else current_user.id
    q = db.query(Notification).filter(Notification.user_id == target_id)
    if unread_only:
        q = q.filter(Notification.is_read == False)  # noqa: E712
    return q.order_by(Notification.created_at.desc()).all()


@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read. Only owner or admin."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notif.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied")
    notif.is_read = True
    db.commit()
    return {"status": "ok"}
