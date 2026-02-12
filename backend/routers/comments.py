"""
Comment CRUD 라우터 (답글 지원).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Comment, CSCase, User, UserRole
from routers.auth import get_current_user
from schemas import CommentCreate, CommentRead
from tasks import notify_comment, notify_reply

router = APIRouter(prefix="/cases/{case_id}/comments", tags=["Comments"])



@router.get("/", response_model=List[CommentRead])
def list_comments(case_id: int, db: Session = Depends(get_db)):
    """Get comments for a case in nested tree structure."""
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    comments = (
        db.query(Comment)
        .options(joinedload(Comment.author), joinedload(Comment.replies).joinedload(Comment.author))
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

    # 알림 생성 (비동기 - Celery task)
    if data.parent_id and parent_comment:
        # 답글: 부모 댓글 작성자에게 알림 (본인 제외)
        notify_reply.delay(case_id, parent_comment.author_id, current_user.name, author_id)
    else:
        # 일반 댓글: 모든 담당자에게 알림 (본인 제외, many-to-many)
        notify_comment.delay(case_id, author_id, comment.content)

    # Reload with author info
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=204)
def delete_comment(
    case_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a comment. Only author or ADMIN can delete."""
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.case_id == case_id
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Permission check: author or ADMIN
    is_author = comment.author_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_author or is_admin):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Delete comment (cascade will handle replies)
    db.delete(comment)
    db.commit()
