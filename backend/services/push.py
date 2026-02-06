"""
Web Push 전송 유틸리티.
Celery task에서 DB 알림 생성 직후 호출하여 OS 레벨 푸시를 전송한다.
"""

import json
import logging
import os

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from models import PushSubscription

logger = logging.getLogger(__name__)

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "")


def send_push_to_user(
    db: Session, user_id: int, title: str, body: str, case_id: int | None = None
) -> int:
    """해당 user의 모든 PushSubscription에 Web Push를 전송한다.

    Returns:
        성공적으로 전송한 구독 수.
    """
    if not VAPID_PRIVATE_KEY or not VAPID_CLAIMS_EMAIL:
        logger.debug("VAPID keys not configured — skipping push")
        return 0

    subscriptions = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user_id)
        .all()
    )
    if not subscriptions:
        return 0

    payload = json.dumps({"title": title, "body": body, "case_id": case_id})
    sent = 0
    expired_ids = []

    for sub in subscriptions:
        try:
            resp = webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_EMAIL},
                ttl=86400,
            )
            sent += 1
        except WebPushException as e:
            status_code = e.response.status_code if e.response is not None else None
            if status_code in (404, 410):
                expired_ids.append(sub.id)
            else:
                logger.error("Web push failed for subscription %s: %s", sub.id, e)
        except Exception as e:
            logger.error("Unexpected push error for subscription %s: %s", sub.id, e)

    # 만료/무효 구독 일괄 삭제
    if expired_ids:
        db.query(PushSubscription).filter(PushSubscription.id.in_(expired_ids)).delete(
            synchronize_session=False
        )
        db.commit()
        logger.info("Cleaned up %d expired push subscriptions", len(expired_ids))

    return sent
