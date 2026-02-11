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

    import numpy as np

    from services.similarity import (
        SIMILARITY_THRESHOLD,
        CaseSimilarityEngine,
        compute_tag_similarity,
        load_model_from_redis,
        save_model_to_redis,
    )

    all_cases = db.query(CSCase).all()
    if not all_cases:
        return []

    engine = load_model_from_redis()
    if engine is None or not engine._fitted:
        if len(all_cases) > 1000:
            return []
        engine = CaseSimilarityEngine()
        engine.fit(
            [c.title for c in all_cases],
            [c.content or "" for c in all_cases],
        )
        save_model_to_redis(engine)

    # Batch transform (sparse matrices)
    target_title_vec = engine.get_title_vector(title)
    target_content_vec = engine.get_content_vector(content)
    all_title_vecs = engine.batch_title_vectors([c.title for c in all_cases])
    all_content_vecs = engine.batch_content_vectors([c.content or "" for c in all_cases])

    title_sims = engine.batch_similarities(target_title_vec, all_title_vecs)
    content_sims = engine.batch_similarities(target_content_vec, all_content_vecs)

    input_tags = tags or []
    combined_scores = np.zeros(len(all_cases))
    for i, case in enumerate(all_cases):
        tag_sim = compute_tag_similarity(input_tags, case.tags or [])
        combined_scores[i] = tag_sim * 0.5 + title_sims[i] * 0.3 + content_sims[i] * 0.2

    # Top 5 via argsort, apply threshold
    top_indices = np.argsort(combined_scores)[::-1][:5]

    results = []
    for i in top_indices:
        score = float(combined_scores[i])
        if score < SIMILARITY_THRESHOLD:
            continue
        c = all_cases[i]
        matched = list(set(t.lower() for t in input_tags) & set(t.lower() for t in (c.tags or [])))
        comment_count = len(c.comments) if c.comments else 0
        results.append(CaseSimilarRead(
            id=c.id,
            title=c.title,
            status=c.status,
            similarity_score=round(score, 4),
            matched_tags=matched,
            comment_count=comment_count,
            resolved_at=c.completed_at,
        ))
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


@router.get("/{case_id}/similar", response_model=List[CaseSimilarRead])
def get_case_similar(
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get similar cases for an existing case. Uses Redis cache, falls back to real-time computation."""
    from services.cache import get_cached_similar_cases
    from services.similarity import (
        SIMILARITY_THRESHOLD,
        CaseSimilarityEngine,
        compute_tag_similarity,
        load_model_from_redis,
        save_model_to_redis,
    )

    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Try Redis cache first
    cached = get_cached_similar_cases(case_id)
    if cached:
        case_ids = [item["case_id"] for item in cached[:5]]
        score_map = {item["case_id"]: item["score"] for item in cached[:5]}
        cases = db.query(CSCase).filter(CSCase.id.in_(case_ids)).all()
        case_map = {c.id: c for c in cases}

        results = []
        for cid in case_ids:
            c = case_map.get(cid)
            if not c:
                continue
            matched = list(set(t.lower() for t in (case.tags or [])) & set(t.lower() for t in (c.tags or [])))
            comment_count = len(c.comments) if c.comments else 0
            results.append(CaseSimilarRead(
                id=c.id,
                title=c.title,
                status=c.status,
                similarity_score=round(score_map[cid], 4),
                matched_tags=matched,
                comment_count=comment_count,
                resolved_at=c.completed_at,
            ))
        return results

    # Fallback: real-time batch computation
    import numpy as np

    all_cases = db.query(CSCase).filter(CSCase.id != case_id).all()
    if not all_cases:
        return []

    engine = load_model_from_redis()
    if engine is None or not engine._fitted:
        if len(all_cases) > 1000:
            return []
        corpus = [case] + all_cases
        engine = CaseSimilarityEngine()
        engine.fit(
            [c.title for c in corpus],
            [c.content or "" for c in corpus],
        )
        save_model_to_redis(engine)

    # Batch transform (sparse matrices)
    target_title_vec = engine.get_title_vector(case.title)
    target_content_vec = engine.get_content_vector(case.content or "")
    all_title_vecs = engine.batch_title_vectors([c.title for c in all_cases])
    all_content_vecs = engine.batch_content_vectors([c.content or "" for c in all_cases])

    title_sims = engine.batch_similarities(target_title_vec, all_title_vecs)
    content_sims = engine.batch_similarities(target_content_vec, all_content_vecs)

    target_tags = case.tags or []
    combined_scores = np.zeros(len(all_cases))
    for i, other in enumerate(all_cases):
        tag_sim = compute_tag_similarity(target_tags, other.tags or [])
        combined_scores[i] = tag_sim * 0.5 + title_sims[i] * 0.3 + content_sims[i] * 0.2

    # Top 5 via argsort, apply threshold
    top_indices = np.argsort(combined_scores)[::-1][:5]

    results = []
    for i in top_indices:
        score = float(combined_scores[i])
        if score < SIMILARITY_THRESHOLD:
            continue
        c = all_cases[i]
        matched = list(set(t.lower() for t in target_tags) & set(t.lower() for t in (c.tags or [])))
        comment_count = len(c.comments) if c.comments else 0
        results.append(CaseSimilarRead(
            id=c.id,
            title=c.title,
            status=c.status,
            similarity_score=round(score, 4),
            matched_tags=matched,
            comment_count=comment_count,
            resolved_at=c.completed_at,
        ))
    return results


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
