"""
CS Case CRUD 라우터.
"""

from datetime import date, datetime
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
    MyProgress, StatByAssignee, StatByStatus, StatByTime,
)
from services.statistics import stat_by_assignee, stat_by_status, stat_by_time
from tasks import compute_case_similarity, learn_tags_from_case, notify_case_assigned

router = APIRouter(prefix="/cases", tags=["CS Cases"])


@router.get("/similar", response_model=List[CaseSimilarRead])
def get_similar_cases(
    title: str = Query("", description="Case title"),
    content: str = Query("", description="Case content"),
    tags: List[str] = Query([], description="Tag list"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Find similar cases using TF-IDF similarity with tag/title/content weighting."""
    if len(title.strip()) < 3 and not content.strip():
        return []

    from services.similarity import find_similar_cases as find_similar

    all_cases = db.query(CSCase).all()
    matches = find_similar(title, content, tags or [], all_cases)
    return [
        CaseSimilarRead(
            id=m["case"].id,
            title=m["case"].title,
            status=m["case"].status,
            similarity_score=m["score"],
            matched_tags=m["matched_tags"],
            comment_count=len(m["case"].comments) if m["case"].comments else 0,
            resolved_at=m["case"].completed_at,
        )
        for m in matches
    ]


@router.get("/", response_model=CaseListResponse)
def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CaseStatus] = None,
    assignee_id: Optional[int] = None,
    product_id: Optional[int] = None,
    requester: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List cases with pagination and optional filters (status, assignee, product, requester).
    Non-admin users only see cases they created or are assigned to."""
    q = db.query(CSCase).options(joinedload(CSCase.assignee), joinedload(CSCase.assignees))

    # Non-admin: only own cases (created or assigned)
    if current_user.role != UserRole.ADMIN:
        q = q.filter(
            (CSCase.requester == current_user.name)
            | (CSCase.assignees.any(User.id == current_user.id))
        )

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

    # Learn tag keyword associations (async)
    if case.tags:
        learn_tags_from_case.delay(case.id)

    # Compute similar cases (async)
    compute_case_similarity.delay(case.id)

    return case


# ======================== Statistics ========================


@router.get("/statistics", response_model=Union[List[StatByAssignee], List[StatByStatus], StatByTime])
def get_statistics(
    by: str = Query(..., description="assignee | status | time"),
    period: Optional[str] = Query(None, description="daily | weekly | monthly"),
    target_date: Optional[date] = Query(None, description="Target date (YYYY-MM-DD)"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """통계 조회 (by: assignee, status, time). Optional period/assignee filter."""
    if by == "assignee":
        return stat_by_assignee(db, period=period, target_date=target_date)
    elif by == "status":
        return stat_by_status(db, period=period, target_date=target_date, assignee_id=assignee_id)
    elif by == "time":
        return stat_by_time(db)
    else:
        raise HTTPException(status_code=400, detail="'by' parameter must be one of: assignee, status, time")


@router.get("/my-progress", response_model=MyProgress)
def get_my_progress(
    target_date: Optional[date] = Query(None, description="Target date (YYYY-MM-DD), defaults to today"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's case counts by status (created or assigned). No date = all-time."""
    from sqlalchemy import case as sa_case, func

    from services.statistics import _compute_date_range

    q = db.query(
        func.sum(sa_case((CSCase.status == CaseStatus.OPEN, 1), else_=0)).label("open_count"),
        func.sum(sa_case((CSCase.status == CaseStatus.IN_PROGRESS, 1), else_=0)).label("in_progress_count"),
        func.sum(sa_case((CSCase.status == CaseStatus.DONE, 1), else_=0)).label("done_count"),
        func.sum(sa_case((CSCase.status == CaseStatus.CANCEL, 1), else_=0)).label("cancel_count"),
    ).filter(
        or_(
            CSCase.requester == current_user.name,
            CSCase.assignees.any(User.id == current_user.id),
        )
    )

    if target_date:
        start, end = _compute_date_range("daily", target_date)
        if start and end:
            q = q.filter(CSCase.created_at >= start, CSCase.created_at <= end)

    row = q.one()

    return MyProgress(
        open_count=row.open_count or 0,
        in_progress_count=row.in_progress_count or 0,
        done_count=row.done_count or 0,
        cancel_count=row.cancel_count or 0,
    )


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


@router.get("/{case_id}/similar", response_model=List[CaseSimilarRead])
def get_case_similar(
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get similar cases for an existing case. Uses Redis cache, falls back to real-time computation."""
    from services.cache import get_cached_similar_cases
    from services.similarity import MAX_SIMILAR_RESULTS, compute_tag_similarity, find_similar_cases as find_similar

    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    target_tags = case.tags or []

    def _build_result(c, score, matched):
        return CaseSimilarRead(
            id=c.id, title=c.title, status=c.status,
            similarity_score=round(score, 4), matched_tags=matched,
            comment_count=len(c.comments) if c.comments else 0,
            resolved_at=c.completed_at,
        )

    # Try Redis cache first
    cached = get_cached_similar_cases(case_id)
    if cached:
        items = cached[:MAX_SIMILAR_RESULTS]
        case_ids = [item["case_id"] for item in items]
        score_map = {item["case_id"]: item["score"] for item in items}
        cases = db.query(CSCase).filter(CSCase.id.in_(case_ids)).all()
        case_map = {c.id: c for c in cases}

        results = []
        tag_set = set(t.lower() for t in target_tags)
        for cid in case_ids:
            c = case_map.get(cid)
            if not c:
                continue
            matched = list(tag_set & set(t.lower() for t in (c.tags or [])))
            results.append(_build_result(c, score_map[cid], matched))
        return results

    # Fallback: real-time computation
    all_cases = db.query(CSCase).filter(CSCase.id != case_id).all()
    matches = find_similar(case.title, case.content or "", target_tags, all_cases)
    return [_build_result(m["case"], m["score"], m["matched_tags"]) for m in matches]


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

    # Learn tag keyword associations (async)
    if case.tags:
        learn_tags_from_case.delay(case.id)

    # Compute similar cases (async)
    compute_case_similarity.delay(case.id)

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
    elif data.status == CaseStatus.CANCEL:
        case.canceled_at = datetime.utcnow()
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
