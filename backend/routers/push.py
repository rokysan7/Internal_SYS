"""
Web Push 구독 관리 라우터.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import PushSubscription
from routers.auth import get_current_user
from schemas import PushSubscriptionCreate, PushSubscriptionDelete, VapidPublicKeyResponse

router = APIRouter(prefix="/push", tags=["Push"])

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")


@router.get("/vapid-public-key", response_model=VapidPublicKeyResponse)
def get_vapid_public_key(current_user=Depends(get_current_user)):
    """VAPID 공개키를 반환한다. 프론트에서 pushManager.subscribe() 시 사용."""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="VAPID public key not configured",
        )
    return {"public_key": VAPID_PUBLIC_KEY}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_push(
    payload: PushSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """브라우저 Push 구독을 등록한다. 동일 endpoint 존재 시 키를 갱신한다."""
    existing = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == payload.endpoint)
        .first()
    )
    if existing:
        existing.user_id = current_user.id
        existing.p256dh = payload.p256dh
        existing.auth = payload.auth
        db.commit()
        return {"message": "Subscription updated"}

    sub = PushSubscription(
        user_id=current_user.id,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth=payload.auth,
    )
    db.add(sub)
    db.commit()
    return {"message": "Subscription created"}


@router.delete("/unsubscribe")
def unsubscribe_push(
    payload: PushSubscriptionDelete,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """브라우저 Push 구독을 해제한다."""
    sub = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.endpoint == payload.endpoint,
            PushSubscription.user_id == current_user.id,
        )
        .first()
    )
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    db.delete(sub)
    db.commit()
    return {"message": "Subscription removed"}
