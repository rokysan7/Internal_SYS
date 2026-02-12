"""
통계 계산 서비스 모듈.
cases 라우터의 statistics 엔드포인트에서 호출하는 비즈니스 로직.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import case as sa_case, func
from sqlalchemy.orm import Session

from models import CaseStatus, CSCase, User, case_assignees
from schemas import StatByAssignee, StatByStatus, StatByTime


def _compute_date_range(
    period: Optional[str] = None,
    target_date: Optional[date] = None,
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Compute (start, end) datetime range for a given period and date."""
    if not period:
        return None, None

    d = target_date or date.today()

    if period == "daily":
        start = datetime(d.year, d.month, d.day, 0, 0, 0)
        end = datetime(d.year, d.month, d.day, 23, 59, 59)
    elif period == "weekly":
        monday = d - timedelta(days=d.weekday())
        sunday = monday + timedelta(days=6)
        start = datetime(monday.year, monday.month, monday.day, 0, 0, 0)
        end = datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59)
    elif period == "monthly":
        start = datetime(d.year, d.month, 1, 0, 0, 0)
        if d.month == 12:
            end = datetime(d.year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            end = datetime(d.year, d.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
    else:
        return None, None

    return start, end


def stat_by_assignee(
    db: Session,
    period: Optional[str] = None,
    target_date: Optional[date] = None,
) -> List[StatByAssignee]:
    """담당자별 미처리/처리중/완료 건수 (many-to-many, single GROUP BY query)."""
    q = (
        db.query(
            User.id.label("assignee_id"),
            User.name.label("assignee_name"),
            func.sum(sa_case((CSCase.status == CaseStatus.OPEN, 1), else_=0)).label("open_count"),
            func.sum(sa_case((CSCase.status == CaseStatus.IN_PROGRESS, 1), else_=0)).label("in_progress_count"),
            func.sum(sa_case((CSCase.status == CaseStatus.DONE, 1), else_=0)).label("done_count"),
            func.sum(sa_case((CSCase.status == CaseStatus.CANCEL, 1), else_=0)).label("cancel_count"),
        )
        .join(case_assignees, User.id == case_assignees.c.user_id)
        .join(CSCase, CSCase.id == case_assignees.c.case_id)
    )

    start, end = _compute_date_range(period, target_date)
    if start and end:
        q = q.filter(CSCase.created_at >= start, CSCase.created_at <= end)

    rows = q.group_by(User.id, User.name).all()
    return [
        StatByAssignee(
            assignee_id=r.assignee_id,
            assignee_name=r.assignee_name,
            open_count=r.open_count,
            in_progress_count=r.in_progress_count,
            done_count=r.done_count,
            cancel_count=r.cancel_count,
        )
        for r in rows
    ]


def stat_by_status(
    db: Session,
    period: Optional[str] = None,
    target_date: Optional[date] = None,
    assignee_id: Optional[int] = None,
) -> List[StatByStatus]:
    """상태별 건수. Optional assignee filter via many-to-many."""
    q = db.query(CSCase.status, func.count(CSCase.id))

    start, end = _compute_date_range(period, target_date)
    if start and end:
        q = q.filter(CSCase.created_at >= start, CSCase.created_at <= end)

    if assignee_id:
        q = q.filter(CSCase.assignees.any(User.id == assignee_id))

    rows = q.group_by(CSCase.status).all()
    return [StatByStatus(status=row[0], count=row[1]) for row in rows]


def stat_by_time(db: Session) -> StatByTime:
    """평균 처리 시간 (완료된 케이스 기준)."""
    row = (
        db.query(
            func.count(CSCase.id).label("total"),
            func.avg(
                func.extract("epoch", CSCase.completed_at)
                - func.extract("epoch", CSCase.created_at)
            ).label("avg_seconds"),
        )
        .filter(
            CSCase.status == CaseStatus.DONE,
            CSCase.completed_at.isnot(None),
        )
        .first()
    )
    if not row or row.total == 0:
        return StatByTime(avg_hours=None, total_completed=0)

    avg_hours = round(row.avg_seconds / 3600, 2)
    return StatByTime(avg_hours=avg_hours, total_completed=row.total)
