"""
통계 계산 서비스 모듈.
cases 라우터의 statistics 엔드포인트에서 호출하는 비즈니스 로직.
"""

from typing import List

from sqlalchemy import case as sa_case, func
from sqlalchemy.orm import Session

from models import CaseStatus, CSCase, User, case_assignees
from schemas import StatByAssignee, StatByStatus, StatByTime


def stat_by_assignee(db: Session) -> List[StatByAssignee]:
    """담당자별 미처리/처리중/완료 건수 (many-to-many, single GROUP BY query)."""
    rows = (
        db.query(
            User.id.label("assignee_id"),
            User.name.label("assignee_name"),
            func.sum(sa_case((CSCase.status == CaseStatus.OPEN, 1), else_=0)).label("open_count"),
            func.sum(sa_case((CSCase.status == CaseStatus.IN_PROGRESS, 1), else_=0)).label("in_progress_count"),
            func.sum(sa_case((CSCase.status == CaseStatus.DONE, 1), else_=0)).label("done_count"),
        )
        .join(case_assignees, User.id == case_assignees.c.user_id)
        .join(CSCase, CSCase.id == case_assignees.c.case_id)
        .group_by(User.id, User.name)
        .all()
    )
    return [
        StatByAssignee(
            assignee_id=r.assignee_id,
            assignee_name=r.assignee_name,
            open_count=r.open_count,
            in_progress_count=r.in_progress_count,
            done_count=r.done_count,
        )
        for r in rows
    ]


def stat_by_status(db: Session) -> List[StatByStatus]:
    """상태별 건수."""
    rows = (
        db.query(CSCase.status, func.count(CSCase.id))
        .group_by(CSCase.status)
        .all()
    )
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
