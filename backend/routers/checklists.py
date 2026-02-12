"""
Checklist CRUD 라우터.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Checklist, CSCase, User
from routers.auth import get_current_user
from schemas import ChecklistCreate, ChecklistRead, ChecklistUpdate

router = APIRouter(tags=["Checklists"])


@router.get(
    "/cases/{case_id}/checklists",
    response_model=List[ChecklistRead],
)
def list_checklists(case_id: int, db: Session = Depends(get_db)):
    """List all checklist items for a case."""
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return (
        db.query(Checklist)
        .options(joinedload(Checklist.author))
        .filter(Checklist.case_id == case_id)
        .all()
    )


@router.post(
    "/cases/{case_id}/checklists",
    response_model=ChecklistRead,
    status_code=201,
)
def create_checklist(
    case_id: int,
    data: ChecklistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new checklist item for a case."""
    case = db.query(CSCase).filter(CSCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    checklist = Checklist(case_id=case_id, author_id=current_user.id, **data.model_dump())
    db.add(checklist)
    db.commit()
    db.refresh(checklist)
    return checklist


@router.patch("/checklists/{checklist_id}", response_model=ChecklistRead)
def update_checklist(
    checklist_id: int,
    data: ChecklistUpdate,
    db: Session = Depends(get_db),
):
    """Toggle checklist item completion status."""
    checklist = (
        db.query(Checklist)
        .options(joinedload(Checklist.author))
        .filter(Checklist.id == checklist_id)
        .first()
    )
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    checklist.is_done = data.is_done
    db.commit()
    db.refresh(checklist)
    return checklist
