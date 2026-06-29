from inspect import isclass
from typing import Any

from maxo import Ctx
from maxo.fsm.state import State, StatesGroup, any_state
from maxo.routing.filters import BaseFilter
from maxo.routing.middlewares.fsm_context import RAW_STATE_KEY

StateType = str | None | State | StatesGroup | type[StatesGroup]


class StateFilter(BaseFilter[Any]):
    __slots__ = ("_states",)

    def __init__(self, *states: StateType) -> None:
        self._states = states

    async def __call__(self, update: Any, ctx: Ctx) -> bool:
        raw_state = ctx.get(RAW_STATE_KEY)

        for state in self._states:
            if (isinstance(state, str) or state is None) and (
                state in (any_state, raw_state)
            ):
                return True
            if isinstance(state, State) and raw_state == state:
                return True
            if isclass(state) and issubclass(state, StatesGroup) and raw_state in state:
                return True

        return False
