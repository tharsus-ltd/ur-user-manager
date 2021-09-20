from app.handlers import Handlers
import pytest

from app.rockets import get_rocket
from app.models import RocketCreate
from app.main import create_rocket


@pytest.mark.asyncio
async def test_rocket_creation(handlers, mocker):

    with mocker.patch.object(Handlers, "send_msg"):

        rocket = await create_rocket(
            RocketCreate(
                num_engines = 4,
                height = 200
            )
        )

        assert rocket.height == 200
        assert rocket.num_engines == 4
        assert rocket.fuel > 0

        assert await get_rocket(rocket.id) == rocket

        Handlers.send_msg.assert_called_once()
