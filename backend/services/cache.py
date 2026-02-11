"""
Redis DB 2 cache layer for similarity results and TF-IDF model storage.
"""

import json
import logging
import os

import redis
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# DB 2 for cache (DB 0 = Celery broker, DB 1 = Celery backend)
cache_redis = redis.from_url(REDIS_URL.replace("/0", "/2"), decode_responses=False)

SIMILAR_CACHE_TTL = 86400  # 24 hours


def cache_similar_cases(case_id: int, results: list[dict], ttl: int = SIMILAR_CACHE_TTL):
    """Cache similar case results as JSON in Redis."""
    key = f"similar:{case_id}"
    cache_redis.set(key, json.dumps(results), ex=ttl)


def get_cached_similar_cases(case_id: int) -> list[dict] | None:
    """Get cached similar cases. Returns None if not cached."""
    key = f"similar:{case_id}"
    data = cache_redis.get(key)
    if data is None:
        return None
    return json.loads(data)


def invalidate_similar_cache(case_id: int):
    """Remove cached similar cases for a given case."""
    key = f"similar:{case_id}"
    cache_redis.delete(key)
