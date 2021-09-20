import pytest

from hypothesis import given, strategies as st

from app.models import RocketCreate
from app.rockets import calc_initial_fuel, calc_rocket_diameter, get_key, get_rocket, set_rocket
from app import MAX_ENGINES, MAX_HEIGHT, MIN_ENGINES, MIN_HEIGHT


@given(st.integers(MIN_ENGINES, MAX_ENGINES))
def test_diameter(e):
    assert calc_rocket_diameter(1) == 4
    assert calc_rocket_diameter(2) == 4
    assert calc_rocket_diameter(3) == 6
    assert calc_rocket_diameter(4) == 8
    assert calc_rocket_diameter(e) > 0


@given(st.integers(MIN_HEIGHT, MAX_HEIGHT), st.integers(MIN_ENGINES, MAX_ENGINES))
def test_fuel_calc(h, e):
    inp = RocketCreate(height=h, num_engines=e)
    assert calc_initial_fuel(inp) > 0


@pytest.mark.asyncio
async def test_set_get_rocket(rocket, handlers):
    assert (await handlers.redis.exists(get_key(rocket.id))) == 0
    await set_rocket(rocket)
    assert (await handlers.redis.exists(get_key(rocket.id))) == 1
    assert rocket == await get_rocket(rocket.id)