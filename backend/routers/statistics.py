"""
통계 API 라우터.
"""

from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import CaseStatus, CSCase, User
from schemas import StatByAssignee, StatByStatus, StatByTime

router = APIRouter(prefix="/cases/statistics", tags=["Statistics"])


@router.get("/", response_model=Union[List[StatByAssignee], List[StatByStatus], StatByTime])
def get_statistics(
    by: str = Query(..., description="assignee | status | time"),
    db: Session = Depends(get_db),
):
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
