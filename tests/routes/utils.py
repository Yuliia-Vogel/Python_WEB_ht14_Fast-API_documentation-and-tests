import fakeredis
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

#використовую @contextmanager для сумісності з with

@contextmanager
def mock_redis():
    # Мокання Redis
    fake_redis = fakeredis.FakeStrictRedis()
    with patch("src.services.auth.redis.StrictRedis", return_value=fake_redis):
        yield fake_redis


@contextmanager
def mock_rate_limiter():
    # Мок FastAPILimiter
    with patch("fastapi_limiter.depends.RateLimiter.__call__", AsyncMock(return_value=None)):
        yield
