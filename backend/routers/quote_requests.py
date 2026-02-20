"""
Quote Request CRUD router (견적 요청 수집/관리).
"""

import os
from datetime import datetime
from math import ceil
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import (
    QuoteRequest,
    QuoteRequestComment,
    QuoteRequestStatus,
    User,
    UserRole,
)
from routers.auth import get_current_user, require_role
from tasks import notify_quote_request_assigned, notify_quote_request_comment
from schemas import (
    QuoteRequestAssigneeUpdate,
    QuoteRequestCollect,
    QuoteRequestCommentCreate,
    QuoteRequestCommentRead,
    QuoteRequestListResponse,
    QuoteRequestRead,
    QuoteRequestStatusUpdate,
    UserRead,
)

router = APIRouter(prefix="/quote-requests", tags=["Quote Requests"])

QUOTE_API_KEY = os.getenv("QUOTE_API_KEY", "")


# ======================== API Key Auth ========================


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key for external system intake."""
    if not QUOTE_API_KEY or x_api_key != QUOTE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ======================== Data Intake ========================


@router.post("/collect", status_code=201)
def collect_quote_request(
    data: QuoteRequestCollect,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    """Receive quote request data from external system and auto-create a QuoteRequest."""
    try:
        received_at = datetime.strptime(data.date_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date_time format. Expected: YYYY-MM-DD HH:MM:SS")

    qr = QuoteRequest(
        received_at=received_at,
        delivery_date=data.delivery_date,
        email_id=data.email_id,
        email=data.email,
        organization=data.organization,
        quote_request=data.quote_request,
        other_request=data.other_request,
        failed_products=data.failed_products,
        additional_request=data.additional_request,
        status=QuoteRequestStatus.OPEN,
    )
    db.add(qr)
    db.flush()

    # Auto-assign users marked as default quote request handlers
    default_assignees = (
        db.query(User)
        .filter(User.is_quote_assignee == True, User.is_active == True)  # noqa: E712
        .all()
    )
    if default_assignees:
        qr.assignees = default_assignees

    db.commit()
    db.refresh(qr)

    if default_assignees:
        notify_quote_request_assigned.delay(qr.id, [u.id for u in default_assignees])

    return {"id": qr.id, "status": "created"}


# ======================== List / Detail ========================


@router.get("/", response_model=QuoteRequestListResponse)
def list_quote_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[QuoteRequestStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List quote requests with pagination. Non-admin sees only assigned requests."""
    q = db.query(QuoteRequest).options(joinedload(QuoteRequest.assignees))

    # Non-admin: only assigned requests
    if current_user.role != UserRole.ADMIN:
        q = q.filter(QuoteRequest.assignees.any(User.id == current_user.id))

    if status:
        q = q.filter(QuoteRequest.status == status)
    if search:
        like = f"%{search}%"
        q = q.filter(
            QuoteRequest.organization.ilike(like)
            | QuoteRequest.quote_request.ilike(like)
        )

    total = q.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = q.order_by(QuoteRequest.created_at.desc()).offset(offset).limit(page_size).all()

    return QuoteRequestListResponse(
        items=[_to_read(qr) for qr in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ======================== Default Assignees Setting ========================


@router.get("/settings/default-assignees", response_model=List[UserRead])
def get_default_assignees(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Get users marked as default quote request assignees."""
    return db.query(User).filter(User.is_quote_assignee == True, User.is_active == True).all()  # noqa: E712


@router.put("/settings/default-assignees")
def set_default_assignees(
    data: QuoteRequestAssigneeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Bulk-set default quote request assignees. Replaces all current defaults."""
    db.query(User).filter(User.is_quote_assignee == True).update(  # noqa: E712
        {User.is_quote_assignee: False}, synchronize_session="fetch"
    )
    if data.assignee_ids:
        db.query(User).filter(User.id.in_(data.assignee_ids), User.is_active == True).update(  # noqa: E712
            {User.is_quote_assignee: True}, synchronize_session="fetch"
        )
    db.commit()

    updated = db.query(User).filter(User.is_quote_assignee == True).all()  # noqa: E712
    return {"default_assignee_ids": [u.id for u in updated]}


# ======================== Detail ========================


@router.get("/{qr_id}", response_model=QuoteRequestRead)
def get_quote_request(
    qr_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a single quote request by ID."""
    qr = (
        db.query(QuoteRequest)
        .options(joinedload(QuoteRequest.assignees), joinedload(QuoteRequest.comments))
        .filter(QuoteRequest.id == qr_id)
        .first()
    )
    if not qr:
        raise HTTPException(status_code=404, detail="Quote request not found")
    return _to_read(qr)


# ======================== Status / Assignees / Delete ========================


@router.patch("/{qr_id}/status", response_model=QuoteRequestRead)
def update_quote_request_status(
    qr_id: int,
    data: QuoteRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update quote request status. Only assignee or ADMIN can change."""
    qr = (
        db.query(QuoteRequest)
        .options(joinedload(QuoteRequest.assignees))
        .filter(QuoteRequest.id == qr_id)
        .first()
    )
    if not qr:
        raise HTTPException(status_code=404, detail="Quote request not found")

    is_assignee = current_user in qr.assignees
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_assignee or is_admin):
        raise HTTPException(status_code=403, detail="Permission denied")

    qr.status = data.status
    if data.status == QuoteRequestStatus.DONE:
        qr.completed_at = datetime.utcnow()
    elif data.status == QuoteRequestStatus.OPEN:
        qr.completed_at = None

    db.commit()
    db.refresh(qr)
    return _to_read(qr)


@router.put("/{qr_id}/assignees", response_model=QuoteRequestRead)
def update_quote_request_assignees(
    qr_id: int,
    data: QuoteRequestAssigneeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set assignees for a quote request. ADMIN only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")

    qr = (
        db.query(QuoteRequest)
        .options(joinedload(QuoteRequest.assignees))
        .filter(QuoteRequest.id == qr_id)
        .first()
    )
    if not qr:
        raise HTTPException(status_code=404, detail="Quote request not found")

    old_ids = set(u.id for u in qr.assignees)
    users = db.query(User).filter(User.id.in_(data.assignee_ids)).all()
    qr.assignees = users
    db.commit()
    db.refresh(qr)

    new_ids = set(data.assignee_ids) - old_ids
    if new_ids:
        notify_quote_request_assigned.delay(qr.id, list(new_ids))

    return _to_read(qr)


@router.delete("/{qr_id}", status_code=204)
def delete_quote_request(
    qr_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a quote request. ADMIN only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin only")

    qr = db.query(QuoteRequest).filter(QuoteRequest.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Quote request not found")

    db.delete(qr)
    db.commit()


# ======================== Comments ========================


@router.get("/{qr_id}/comments", response_model=List[QuoteRequestCommentRead])
def list_quote_request_comments(
    qr_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get comments for a quote request in nested tree structure."""
    qr = db.query(QuoteRequest).filter(QuoteRequest.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Quote request not found")

    comments = (
        db.query(QuoteRequestComment)
        .options(
            joinedload(QuoteRequestComment.author),
            joinedload(QuoteRequestComment.replies).joinedload(QuoteRequestComment.author),
        )
        .filter(QuoteRequestComment.quote_request_id == qr_id, QuoteRequestComment.parent_id.is_(None))
        .order_by(QuoteRequestComment.created_at.asc())
        .all()
    )
    return comments


@router.post("/{qr_id}/comments", response_model=QuoteRequestCommentRead, status_code=201)
def create_quote_request_comment(
    qr_id: int,
    data: QuoteRequestCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a comment or reply on a quote request."""
    qr = db.query(QuoteRequest).filter(QuoteRequest.id == qr_id).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Quote request not found")

    if data.parent_id:
        parent = db.query(QuoteRequestComment).filter(
            QuoteRequestComment.id == data.parent_id,
            QuoteRequestComment.quote_request_id == qr_id,
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")

    comment = QuoteRequestComment(
        quote_request_id=qr_id,
        author_id=current_user.id,
        content=data.content,
        parent_id=data.parent_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    notify_quote_request_comment.delay(qr_id, current_user.id, data.content)

    return comment


@router.delete("/{qr_id}/comments/{comment_id}", status_code=204)
def delete_quote_request_comment(
    qr_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a comment. Only author or ADMIN can delete."""
    comment = db.query(QuoteRequestComment).filter(
        QuoteRequestComment.id == comment_id,
        QuoteRequestComment.quote_request_id == qr_id,
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    is_author = comment.author_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_author or is_admin):
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(comment)
    db.commit()


# ======================== Helpers ========================


def _to_read(qr: QuoteRequest) -> QuoteRequestRead:
    """Convert QuoteRequest ORM instance to QuoteRequestRead schema."""
    return QuoteRequestRead(
        id=qr.id,
        received_at=qr.received_at,
        delivery_date=qr.delivery_date,
        email_id=qr.email_id,
        email=qr.email,
        organization=qr.organization,
        quote_request=qr.quote_request,
        other_request=qr.other_request,
        failed_products=qr.failed_products,
        additional_request=qr.additional_request,
        status=qr.status,
        created_at=qr.created_at,
        completed_at=qr.completed_at,
        assignee_ids=qr.assignee_ids,
        assignee_names=qr.assignee_names,
        comment_count=len(qr.comments) if qr.comments else 0,
    )
