import pytest

from datetime import timedelta

from app.models import User
from app.security import create_access_token, get_current_user, set_user, user_exists


@pytest.fixture
def access_token():
    access_token_expires = timedelta(minutes=2)
    return create_access_token(data={"sub": "test"}, expires_delta=access_token_expires)


def test_create_access_token(access_token):
    assert access_token


@pytest.mark.asyncio
async def test_decode_access_token(handlers, access_token):
    assert not await user_exists("test")
    await set_user("test", "1234")
    assert await user_exists("test")
    user: User = await get_current_user(access_token)
    assert user.username == "test"
