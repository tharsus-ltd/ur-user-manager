import pytest

from app import __version__, __service__
from app.main import root, get_status


@pytest.mark.asyncio
async def test_root():
    assert await root() == {'Service': __service__, 'Version': __version__}


@pytest.mark.asyncio
async def test_status():
    assert await get_status() is False


# @pytest.mark.asyncio
# async def test_root(handlers, mocker):

#     with mocker.patch.object(Handlers, "send_msg"):

#         rocket = await create_rocket(
#             RocketCreate(
#                 num_engines = 4,
#                 height = 200
#             )
#         )

#         assert rocket.height == 200
#         assert rocket.num_engines == 4
#         assert rocket.fuel > 0

#         assert await get_rocket(rocket.id) == rocket

#         Handlers.send_msg.assert_called_once()
