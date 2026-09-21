"""Rate limiting utilities using Redis sliding window, with memory fallback."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status

from app.config.settings import get_settings


class InMemoryRateLimiter:
    """In-memory rate limiter fallback when Redis is not available or for tests."""

    def __init__(self) -> None:
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        # Clean expired timestamps
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        if len(self._requests[key]) >= limit:
            return True
        self._requests[key].append(now)
        return False


_memory_limiter = InMemoryRateLimiter()
_redis_client: aioredis.Redis | None = None


async def get_redis_limiter() -> aioredis.Redis | None:
    """Get or initialize Redis connection for rate limiting."""
    global _redis_client
    settings = get_settings()
    if settings.is_testing:
        return None
    if _redis_client is None:
        try:
            _redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception:
            _redis_client = None
    return _redis_client


def parse_rate_limit(rate_str: str) -> tuple[int, int]:
    """Parse '20/minute' or '10/second' into (limit, window_seconds)."""
    parts = rate_str.strip().split("/")
    limit = int(parts[0])
    unit = parts[1].lower() if len(parts) > 1 else "minute"

    unit_map = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }
    window = unit_map.get(unit, 60)
    return limit, window


def rate_limit(rate_spec: str) -> Callable:
    """FastAPI dependency for endpoint rate limiting."""
    limit, window_seconds = parse_rate_limit(rate_spec)

    async def dependency(request: Request) -> None:
        settings = get_settings()
        if settings.is_testing:
            return

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"rate_limit:{path}:{client_ip}"

        redis_client = await get_redis_limiter()
        if redis_client:
            try:
                now = time.time()
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, now - window_seconds)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, window_seconds)
                results = await pipe.execute()
                current_count = results[1]
                if current_count >= limit:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later.",
                    )
                return
            except HTTPException:
                raise
            except Exception:
                # Fall back to memory limiter on Redis error
                pass

        if _memory_limiter.is_rate_limited(key, limit, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

    return dependency
