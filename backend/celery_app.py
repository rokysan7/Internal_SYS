"""
Celery 앱 설정 (브로커: Redis).
"""

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "cs_notifications",
    broker=REDIS_URL,
    backend=REDIS_URL.replace("/0", "/1"),
    include=["tasks"],
)

celery.conf.update(
    result_expires=3600,
    timezone="Asia/Seoul",
    beat_schedule={
        "check-pending-cases-every-hour": {
            "task": "tasks.check_pending_cases",
            "schedule": 3600.0,
        },
    },
)
