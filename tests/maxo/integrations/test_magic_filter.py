from typing import Any

import pytest
from magic_filter import F

from maxo import Ctx
from maxo.integrations.magic_filter import MagicData, MagicFilter, check_flags
from maxo.routing.flags import HANDLER_KEY, flags
from maxo.routing.handlers.update import UpdateHandler
from maxo.types import MessageCreated
from tests.factories import make_flagged_handler


class TestCheckFlags:
    @pytest.mark.parametrize(
        ("handler_flags", "magic", "expected"),
        [
            ({}, F.test, None),
            ({"test": True}, F.test, True),
            ({"test": True}, F.spam, None),
            ({"test": {"spam": "eggs"}}, F.test, {"spam": "eggs"}),
        ],
    )
    def test_check_flags(
        self,
        handler_flags: dict[str, Any],
        magic: Any,
        expected: Any,
    ) -> None:
        ctx = Ctx({HANDLER_KEY: make_flagged_handler(**handler_flags)})

        assert check_flags(ctx, magic) == expected

    def test_nested_attribute_access(self) -> None:
        @flags.chat_action(action="typing_on", interval=1)
        async def func(update: MessageCreated) -> None:
            pass

        ctx = Ctx({HANDLER_KEY: UpdateHandler(func)})

        assert check_flags(ctx, F.chat_action.action) == "typing_on"


async def test_magic_filter_custom_cast() -> None:
    magic_filter = MagicFilter(F["item"].cast(str), result_key="result")

    ctx = Ctx({})
    result = await magic_filter({"item": 42}, ctx)

    assert result is True
    assert "result" in ctx
    assert ctx["result"] == "42"
    assert isinstance(ctx["result"], str)


async def test_magic_data_custom_cast() -> None:
    magic_data = MagicData(F["item"].cast(str), result_key="result")

    ctx = Ctx({"item": 42})
    result = await magic_data(None, ctx)

    assert result is True
    assert "result" in ctx
    assert ctx["result"] == "42"
    assert isinstance(ctx["result"], str)
