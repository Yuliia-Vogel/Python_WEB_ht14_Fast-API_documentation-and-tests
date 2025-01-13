from unittest.mock import AsyncMock, patch

def mock_redis():
    # Мокання клієнта Redis
    return patch("redis.asyncio.Redis", AsyncMock)

def mock_rate_limiter():
    # Мокання FastAPILimiter
    return patch("fastapi_limiter.depends.RateLimiter.__call__", AsyncMock(return_value=None))