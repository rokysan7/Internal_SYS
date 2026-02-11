"""
Tag search and suggestion API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import User
from routers.auth import get_current_user
from schemas import TagSearchResult, TagSuggestResult
from services.tag_service import search_tags, suggest_tags

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/search", response_model=List[TagSearchResult])
def tag_search(
    q: str = Query(..., min_length=1, description="Tag name prefix to search"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Search tags by prefix for auto-complete dropdown."""
    return search_tags(q, db)


@router.get("/suggest", response_model=List[TagSuggestResult])
def tag_suggest(
    title: str = Query(..., description="Case title for tag suggestion"),
    content: str = Query("", description="Case content for tag suggestion"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Suggest tags based on case title and content keyword matching."""
    return suggest_tags(title, content, db)
