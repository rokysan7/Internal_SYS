"""
CS Case CRUD 라우터.
"""

from datetime import datetime
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import CaseStatus, CSCase, Notification, NotificationType, User, UserRole
from routers.auth import get_current_user
from math import ceil
from schemas import (
    CaseCreate, CaseRead, CaseListResponse, CaseStatusUpdate, CaseSimilarRead, CaseUpdate,
    StatByAssignee, StatByStatus, StatByTime,
)

router = APIRouter(prefix="/cases", tags=["CS Cases"])


@router.get("/similar", response_model=List[CaseSimilarRead])
def get_similar_cases(
    query: str = Query(..., description="검색 쿼리 (제목/내용 기반)"),
    db: Session = Depends(get_db),
):
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
    db: Session = Depends(get_db),
):
    q = db.query(CSCase).options(joinedload(CSCase.assignee))
    if status:
        q = q.filter(CSCase.status == status)
    if assignee_id:
        q = q.filter(CSCase.assignee_id == assignee_id)
    if product_id:
        q = q.filter(CSCase.product_id == product_id)

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
def create_case(data: CaseCreate, db: Session = Depends(get_db)):
    case = CSCase(**data.model_dump())
    db.add(case)
    db.commit()
    db.refresh(case)

    # 담당자 지정 시 알림 자동 생성
    if case.assignee_id:
        notif = Notification(
            user_id=case.assignee_id,
            case_id=case.id,
            message=f"CS Case #{case.id} '{case.title}' 담당으로 배정되었습니다.",
            type=NotificationType.ASSIGNEE,
        )
        db.add(notif)
        db.commit()

    return case


# ======================== Statistics ========================


@router.get("/statistics", response_model=Union[List[StatByAssignee], List[StatByStatus], StatByTime])
def get_statistics(
    by: str = Query(..., description="assignee | status | time"),
    db: Session = Depends(get_db),
):
    """통계 조회 (by: assignee, status, time)"""
    if by == "assignee":
        return _stat_by_assignee(db)
    elif by == "status":
        return _stat_by_status(db)
    elif by == "time":
        return _stat_by_time(db)
    else:
        raise HTTPException(status_code=400, detail="by 파라미터는 assignee, status, time 중 하나여야 합니다.")


def _stat_by_assignee(db: Session) -> List[StatByAssignee]:
    """담당자별 미처리/처리중/완료 건수."""
    users = db.query(User).all()
    results = []
    for user in users:
        cases = db.query(CSCase).filter(CSCase.assignee_id == user.id).all()
        open_count = sum(1 for c in cases if c.status == CaseStatus.OPEN)
        in_progress = sum(1 for c in cases if c.status == CaseStatus.IN_PROGRESS)
        done = sum(1 for c in cases if c.status == CaseStatus.DONE)
        if open_count + in_progress + done > 0:
            results.append(
                StatByAssignee(
                    assignee_id=user.id,
                    assignee_name=user.name,
                    open_count=open_count,
                    in_progress_count=in_progress,
                    done_count=done,
                )
            )
    return results


def _stat_by_status(db: Session) -> List[StatByStatus]:
    """상태별 건수."""
    rows = (
        db.query(CSCase.status, func.count(CSCase.id))
        .group_by(CSCase.status)
        .all()
    )
    return [StatByStatus(status=row[0], count=row[1]) for row in rows]


def _stat_by_time(db: Session) -> StatByTime:
    """평균 처리 시간 (완료된 케이스 기준)."""
    completed = (
        db.query(CSCase)
        .filter(
            CSCase.status == CaseStatus.DONE,
            CSCase.completed_at.isnot(None),
        )
        .all()
    )
    total = len(completed)
    if total == 0:
        return StatByTime(avg_hours=None, total_completed=0)

    total_hours = sum(
        (c.completed_at - c.created_at).total_seconds() / 3600
        for c in completed
    )
    return StatByTime(avg_hours=round(total_hours / total, 2), total_completed=total)


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = (
        db.query(CSCase)
        .options(joinedload(CSCase.assignee))
        .filter(CSCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=CaseRead)
def update_case(case_id: int, data: CaseUpdate, db: Session = Depends(get_db)):
    case = (
        db.query(CSCase)
        .options(joinedload(CSCase.assignee))
        .filter(CSCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    old_assignee_id = case.assignee_id
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(case, key, value)
    db.commit()
    db.refresh(case)

    # 담당자가 변경된 경우 알림 생성
    if case.assignee_id and case.assignee_id != old_assignee_id:
        notif = Notification(
            user_id=case.assignee_id,
            case_id=case.id,
            message=f"CS Case #{case.id} '{case.title}' 담당으로 배정되었습니다.",
            type=NotificationType.ASSIGNEE,
        )
        db.add(notif)
        db.commit()

    # Reload with assignee for response
    db.refresh(case)
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
        .options(joinedload(CSCase.assignee))
        .filter(CSCase.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Permission check
    is_assignee = case.assignee_id == current_user.id
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
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Permission check: assignee or ADMIN
    is_assignee = case.assignee_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_assignee or is_admin):
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(case)
    db.commit()
