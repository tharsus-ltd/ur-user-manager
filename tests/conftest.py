import uuid
import pytest
import fakeredis.aioredis

from app.models import Rocket, RocketCreate
from app.rockets import calc_initial_fuel
from app.handlers import Handlers


@pytest.fixture
def handlers():
    handlers = Handlers()
    handlers.redis = fakeredis.aioredis.FakeRedis()
    return handlers


@pytest.fixture
def rocket():
    cr = RocketCreate(
        height=200,
        num_engines=4,
    )
    return Rocket(
        **cr.dict(),
        id=str(uuid.uuid4()),
        fuel=calc_initial_fuel(cr)
    )