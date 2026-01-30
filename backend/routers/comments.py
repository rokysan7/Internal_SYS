"""
Comment CRUD 라우터 (답글 지원).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Comment, CSCase, Notification, NotificationType, User
from routers.auth import get_current_user
from schemas import CommentCreate, CommentRead

router = APIRouter(prefix="/cases/{case_id}/comments", tags=["Comments"])


def build_comment_tree(comments: List[Comment]) -> List[Comment]:
    """Build nested comment tree from flat list."""
    comment_map = {c.id: c for c in comments}
    roots = []

    for comment in comments:
        if comment.parent_id is None:
            roots.append(comment)
        else:
            parent = comment_map.get(comment.parent_id)
            if parent:
                if not hasattr(parent, '_replies'):
                    parent._replies = []
                parent._replies.append(comment)

    return roots


@router.get("/", response_model=List[CommentRead])
def list_comments(case_id: int, db: Session = Depends(get_db)):
    """Get comments for a case in nested tree structure."""
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Load all comments with author info, then build tree
    comments = (
        db.query(Comment)
        .options(joinedload(Comment.author))
        .filter(Comment.case_id == case_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.asc())
        .all()
    )

    return comments


@router.post("/", response_model=CommentRead, status_code=201)
def create_comment(
    case_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a comment or reply."""
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Validate parent_id if provided
    parent_comment = None
    if data.parent_id:
        parent_comment = db.query(Comment).filter(
            Comment.id == data.parent_id,
            Comment.case_id == case_id
        ).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    author_id = current_user.id
    comment = Comment(case_id=case_id, author_id=author_id, **data.model_dump())
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # 알림 생성 (동기 방식 - Celery 불필요)
    if data.parent_id and parent_comment:
        # 답글: 부모 댓글 작성자에게 알림 (본인 제외)
        if parent_comment.author_id != author_id:
            notif = Notification(
                user_id=parent_comment.author_id,
                case_id=case_id,
                message=f"{current_user.name}님이 회원님의 댓글에 답글을 남겼습니다.",
                type=NotificationType.COMMENT,
            )
            db.add(notif)
            db.commit()
    else:
        # 일반 댓글: 담당자에게 알림 (본인 제외)
        if case.assignee_id and case.assignee_id != author_id:
            notif = Notification(
                user_id=case.assignee_id,
                case_id=case_id,
                message=f"CS Case #{case.id}에 새로운 댓글: {comment.content[:50]}",
                type=NotificationType.COMMENT,
            )
            db.add(notif)
            db.commit()

    # Reload with author info
    db.refresh(comment)
    return comment
