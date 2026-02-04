"""
CS Case CRUD 라우터.
"""

from datetime import datetime
from math import ceil
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import CaseStatus, CSCase, User, UserRole
from routers.auth import get_current_user
from schemas import (
    CaseCreate, CaseRead, CaseListResponse, CaseStatusUpdate, CaseSimilarRead, CaseUpdate,
    StatByAssignee, StatByStatus, StatByTime,
)
from services.statistics import stat_by_assignee, stat_by_status, stat_by_time
from tasks import notify_case_assigned

router = APIRouter(prefix="/cases", tags=["CS Cases"])


@router.get("/similar", response_model=List[CaseSimilarRead])
def get_similar_cases(
    query: str = Query(..., description="검색 쿼리 (제목/내용 기반)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Search for similar cases by title or content keyword match."""
    results = (
        db.query(CSCase)
        .filter(
            or_(
                CSCase.title.ilike(f"%{query}%"),
                CSCase.content.ilike(f"%{query}%"),
            )
        )
        .order_by(CSCase.created_at.desc())
        .limit(10)
        .all()
    )
    return results


@router.get("/", response_model=CaseListResponse)
def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CaseStatus] = None,
    assignee_id: Optional[int] = None,
    product_id: Optional[int] = None,
    requester: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List cases with pagination and optional filters (status, assignee, product, requester)."""
    q = db.query(CSCase).options(joinedload(CSCase.assignee), joinedload(CSCase.assignees))
    if status:
        q = q.filter(CSCase.status == status)
    if assignee_id:
        q = q.filter(CSCase.assignees.any(User.id == assignee_id))
    if product_id:
        q = q.filter(CSCase.product_id == product_id)
    if requester:
        q = q.filter(CSCase.requester == requester)

    total = q.count()
    total_pages = ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = q.order_by(CSCase.created_at.desc()).offset(offset).limit(page_size).all()

    return CaseListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=CaseRead, status_code=201)
def create_case(
    data: CaseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new CS case with optional assignees. Sends notification to assignees."""
    case_data = data.model_dump(exclude={"assignee_ids"})
    assignee_ids = data.assignee_ids or []

    # Set assignee_id to first assignee for backward compat
    if assignee_ids:
        case_data["assignee_id"] = assignee_ids[0]

    case = CSCase(**case_data)
    db.add(case)
    db.flush()

    # Add many-to-many assignees
    if assignee_ids:
        users = db.query(User).filter(User.id.in_(assignee_ids)).all()
        case.assignees = users

    db.commit()
    db.refresh(case)

    # Send notifications to ALL assignees (async)
    if assignee_ids:
        notify_case_assigned.delay(case.id, assignee_ids)

    return case


# ======================== Statistics ========================


@router.get("/statistics", response_model=Union[List[StatByAssignee], List[StatByStatus], StatByTime])
def get_statistics(
    by: str = Query(..., description="assignee | status | time"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """통계 조회 (by: assignee, status, time)"""
    if by == "assignee":
        return stat_by_assignee(db)
    elif by == "status":
        return stat_by_status(db)
    elif by == "time":
        return stat_by_time(db)
    else:
        raise HTTPException(status_code=400, detail="'by' parameter must be one of: assignee, status, time")


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a single case by ID with assignee details."""
    case = (
        db.query(CSCase)
        .options(joinedload(CSCase.assignee), joinedload(CSCase.assignees))
        .filter(CSCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: int,
    data: CaseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update case fields. Sends notification to newly added assignees."""
    case = (
        db.query(CSCase)
        .options(joinedload(CSCase.assignee), joinedload(CSCase.assignees))
        .filter(CSCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    old_assignee_ids = set(u.id for u in case.assignees)
    update_data = data.model_dump(exclude_unset=True)

    # Handle assignee_ids separately from other fields
    new_assignee_ids = update_data.pop("assignee_ids", None)

    for key, value in update_data.items():
        setattr(case, key, value)

    # Update many-to-many assignees if provided
    if new_assignee_ids is not None:
        users = db.query(User).filter(User.id.in_(new_assignee_ids)).all()
        case.assignees = users
        # Set assignee_id to first assignee for backward compat
        case.assignee_id = new_assignee_ids[0] if new_assignee_ids else None

    db.commit()
    db.refresh(case)

    # Send notifications to newly added assignees (async)
    if new_assignee_ids is not None:
        added_ids = set(new_assignee_ids) - old_assignee_ids
        if added_ids:
            notify_case_assigned.delay(case.id, list(added_ids))

    return case


@router.patch("/{case_id}/status", response_model=CaseRead)
def update_case_status(
    case_id: int,
    data: CaseStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update case status. Only assignee or ADMIN can change status."""
    case = (
        db.query(CSCase)
        .options(joinedload(CSCase.assignee), joinedload(CSCase.assignees))
        .filter(CSCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Permission check
    is_assignee = current_user in case.assignees
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_assignee or is_admin):
        raise HTTPException(status_code=403, detail="Permission denied")

    case.status = data.status
    if data.status == CaseStatus.DONE:
        case.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a case. Only assignee or ADMIN can delete."""
    case = (
        db.query(CSCase)
        .options(joinedload(CSCase.assignees))
        .filter(CSCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Permission check: assignee or ADMIN
    is_assignee = current_user in case.assignees
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_assignee or is_admin):
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(case)
    db.commit()
