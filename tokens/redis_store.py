"""
ذخیره و مدیریت کدهای ۵رقمی توکن در Redis.

کلید: fitopia:gym_token:{code}
مقدار: JSON شامل token_id و metadata
TTL: تا نیمه‌شب همان روز (بر اساس TIME_ZONE پروژه)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, time, timedelta
from typing import Any, Optional

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

KEY_PREFIX = "fitopia:gym_token:"
_redis_client = None
_redis_unavailable = False


def next_midnight(now=None):
    """اولین نیمه‌شب بعدی در TIME_ZONE فعلی پروژه."""
    if now is None:
        now = timezone.now()
    local = timezone.localtime(now)
    tomorrow = local.date() + timedelta(days=1)
    midnight_naive = datetime.combine(tomorrow, time.min)
    return timezone.make_aware(midnight_naive, timezone.get_current_timezone())


def seconds_until_midnight(now=None) -> int:
    target = next_midnight(now)
    if now is None:
        now = timezone.now()
    delta = int((target - now).total_seconds())
    return max(delta, 1)


def _get_client():
    global _redis_client, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis

        client = redis.Redis.from_url(
            getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0"),
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
        )
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable for gym tokens: %s", exc)
        if getattr(settings, "REDIS_OPTIONAL", True):
            _redis_unavailable = True
            return None
        raise


def _key(code: str) -> str:
    return f"{KEY_PREFIX}{code}"


def store_token(code: str, payload: dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
    """ذخیره توکن فعال در Redis تا نیمه‌شب."""
    client = _get_client()
    if client is None:
        return False
    if ttl_seconds is None:
        ttl_seconds = seconds_until_midnight()
    try:
        client.setex(_key(code), ttl_seconds, json.dumps(payload, default=str))
        return True
    except Exception as exc:
        logger.warning("Failed to store token in Redis: %s", exc)
        return False


def get_token(code: str) -> Optional[dict[str, Any]]:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(_key(code))
        if not raw:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Failed to read token from Redis: %s", exc)
        return None


def delete_token(code: str) -> bool:
    client = _get_client()
    if client is None:
        return False
    try:
        client.delete(_key(code))
        return True
    except Exception as exc:
        logger.warning("Failed to delete token from Redis: %s", exc)
        return False


def exists(code: str) -> bool:
    client = _get_client()
    if client is None:
        return False
    try:
        return bool(client.exists(_key(code)))
    except Exception:
        return False
