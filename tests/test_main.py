import pytest

from app import __version__, __service__
from app.main import get_all_users, root, get_status
from app.security import set_user


@pytest.mark.asyncio
async def test_root():
    assert await root() == {'Service': __service__, 'Version': __version__}


@pytest.mark.asyncio
async def test_status():
    assert await get_status() is False


@pytest.mark.asyncio
async def test_get_users(handlers):
    assert await get_all_users() == []

    await set_user("test1", "123")
    await set_user("test2", "123")
    await set_user("test3", "123")

    users = await get_all_users()

    assert len(users) == 3
