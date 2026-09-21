from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque

try:
    import redis
except Exception:  # pragma: no cover - optional dependency
    redis = None

from sentinel.config import settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit_per_minute: int) -> bool:
        now = time.time()
        window_start = now - 60.0
        bucket = self._hits[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= limit_per_minute:
            return False
        bucket.append(now)
        return True


class RedisRateLimiter:
    def __init__(self, url: str, password: str | None = None) -> None:
        if redis is None:
            raise RuntimeError("redis package not available")
        self.client = redis.Redis.from_url(url, password=password, decode_responses=True)

    def allow(self, key: str, limit_per_minute: int) -> bool:
        bucket = f"sentinel:rl:{key}:{int(time.time() // 60)}"
        count = self.client.incr(bucket)
        if count == 1:
            self.client.expire(bucket, 70)
        return count <= limit_per_minute


def build_rate_limiter():
    if settings.redis_url and redis is not None:
        return RedisRateLimiter(settings.redis_url, settings.redis_password)
    return InMemoryRateLimiter()
