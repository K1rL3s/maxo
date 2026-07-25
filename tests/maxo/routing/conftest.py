from typing import Any

import pytest

from maxo import Bot, Ctx
from maxo.routing.filters import BaseFilter
from maxo.types import MessageCreated
from tests.mocks import MockBot


class WritingFilter(BaseFilter[MessageCreated]):
    """Проходящий фильтр, который пишет в ctx."""

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        ctx["command"] = "start"
        return True


class FalseFilter(BaseFilter[MessageCreated]):
    """Фильтр, который всегда не проходит."""

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        return False


class WritingFalseFilter(BaseFilter[MessageCreated]):
    """Фильтр, который пишет в ctx, но не проходит."""

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        ctx["command"] = "start"
        return False


@pytest.fixture
def bot() -> MockBot:
    return MockBot()


@pytest.fixture
def ctx(update: Any, bot: Bot) -> Ctx:
    ctx = Ctx({"update": update, "bot": bot})
    ctx["ctx"] = ctx
    return ctx
