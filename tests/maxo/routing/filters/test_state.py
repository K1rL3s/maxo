import pytest

from maxo import Ctx
from maxo.fsm.state import State, StatesGroup, any_state
from maxo.routing.filters.state import StateFilter
from maxo.routing.middlewares.fsm_context import RAW_STATE_KEY


class Form(StatesGroup):
    name = State()
    age = State()


async def test_state_filter_matches_raw_state_string() -> None:
    state_filter = StateFilter("Form:name")

    assert await state_filter(None, Ctx({RAW_STATE_KEY: "Form:name"})) is True


async def test_state_filter_matches_none_state() -> None:
    state_filter = StateFilter(None)

    assert await state_filter(None, Ctx({RAW_STATE_KEY: None})) is True


async def test_state_filter_matches_any_state() -> None:
    state_filter = StateFilter(any_state)

    assert await state_filter(None, Ctx({RAW_STATE_KEY: any_state})) is True


async def test_state_filter_matches_state_instance() -> None:
    state_filter = StateFilter(Form.name)

    assert await state_filter(None, Ctx({RAW_STATE_KEY: Form.name})) is True


async def test_state_filter_matches_states_group() -> None:
    state_filter = StateFilter(Form)

    assert await state_filter(None, Ctx({RAW_STATE_KEY: "Form:age"})) is True


async def test_state_filter_returns_false_on_miss() -> None:
    state_filter = StateFilter(Form)

    assert await state_filter(None, Ctx({RAW_STATE_KEY: "Other:state"})) is False


def test_state_filter_requires_states() -> None:
    with pytest.raises(ValueError, match="At least one state is required"):
        StateFilter()
