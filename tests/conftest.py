import pytest
import fakeredis.aioredis

from app.handlers import Handlers


@pytest.fixture
def handlers():
    handlers = Handlers()
    handlers.redis = fakeredis.aioredis.FakeRedis()
    return handlers
