import pytest

from app import __version__, __service__
from app.main import root, get_status


@pytest.mark.asyncio
async def test_root():
    assert await root() == {'Service': __service__, 'Version': __version__}


@pytest.mark.asyncio
async def test_status():
    assert await get_status() is False
