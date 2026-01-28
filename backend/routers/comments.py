"""
Comment CRUD 라우터.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Comment, CSCase
from schemas import CommentCreate, CommentRead
from tasks import notify_comment

router = APIRouter(prefix="/cases/{case_id}/comments", tags=["Comments"])


@router.get("/", response_model=List[CommentRead])
def list_comments(case_id: int, db: Session = Depends(get_db)):
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return (
        db.query(Comment)
        .filter(Comment.case_id == case_id)
        .order_by(Comment.created_at.asc())
        .all()
    )


@router.post("/", response_model=CommentRead, status_code=201)
def create_comment(
    case_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db),
):
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # TODO: author_id는 인증 구현 후 토큰에서 추출. 현재는 임시로 1 사용.
    author_id = 1
    comment = Comment(case_id=case_id, author_id=author_id, **data.model_dump())
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # 댓글 작성 시 담당자에게 비동기 알림 (Celery)
    if case.assignee_id and case.assignee_id != author_id:
        notify_comment.delay(case_id, author_id, comment.content)

    return comment
