from __future__ import annotations

import threading
import time
from functools import lru_cache

from fastapi import HTTPException, status
from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings


class RateLimiter:
    def __init__(self) -> None:
        self._fallback_store: dict[str, tuple[int, float]] = {}
        self._fallback_lock = threading.Lock()
        self._redis_client: Redis | None = None
        self._redis_disabled = False

    def ensure_within_limit(self, keys: list[str], limit: int, window_seconds: int, detail: str) -> None:
        retry_after = 0
        for key in keys:
            count, ttl = self._get_state(key)
            if count < limit:
                continue
            retry_after = max(retry_after, ttl)

        if retry_after > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail,
                headers={"Retry-After": str(retry_after)},
            )

    def record_failure(self, keys: list[str], window_seconds: int) -> None:
        for key in keys:
            self._increment(key, window_seconds)

    def reset(self, keys: list[str]) -> None:
        for key in keys:
            self._delete(key)

    def _get_state(self, key: str) -> tuple[int, int]:
        client = self._redis()
        if client is not None:
            try:
                raw_count = client.get(key)
                if raw_count is None:
                    return 0, 0
                ttl = client.ttl(key)
                return int(raw_count), max(int(ttl), 0)
            except RedisError:
                self._redis_disabled = True

        with self._fallback_lock:
            count, expires_at = self._fallback_store.get(key, (0, 0.0))
            now = time.time()
            if expires_at <= now:
                self._fallback_store.pop(key, None)
                return 0, 0
            return count, max(int(expires_at - now), 0)

    def _increment(self, key: str, window_seconds: int) -> None:
        client = self._redis()
        if client is not None:
            try:
                pipe = client.pipeline()
                pipe.incr(key)
                pipe.ttl(key)
                count, ttl = pipe.execute()
                if int(ttl) < 0:
                    client.expire(key, window_seconds)
                return
            except RedisError:
                self._redis_disabled = True

        with self._fallback_lock:
            now = time.time()
            count, expires_at = self._fallback_store.get(key, (0, now + window_seconds))
            if expires_at <= now:
                count = 0
                expires_at = now + window_seconds
            self._fallback_store[key] = (count + 1, expires_at)

    def _delete(self, key: str) -> None:
        client = self._redis()
        if client is not None:
            try:
                client.delete(key)
                return
            except RedisError:
                self._redis_disabled = True

        with self._fallback_lock:
            self._fallback_store.pop(key, None)

    def _redis(self) -> Redis | None:
        if self._redis_disabled:
            return None
        if self._redis_client is not None:
            return self._redis_client

        try:
            client = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.5, socket_timeout=0.5)
            client.ping()
        except RedisError:
            self._redis_disabled = True
            return None

        self._redis_client = client
        return client


@lru_cache
def get_rate_limiter() -> RateLimiter:
    return RateLimiter()
