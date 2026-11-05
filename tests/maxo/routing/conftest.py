from typing import Any

import pytest

from maxo import Bot, Ctx
from maxo.routing.ctx import CTX_KEY
from maxo.routing.filters import BaseFilter
from maxo.types import MessageCreated
from tests.mocks import MockBot


class WritingFilter(BaseFilter[MessageCreated]):
    """Проходящий фильтр, который пишет в ctx."""

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        ctx["command"] = "start"
        return True


class WritingFalseFilter(BaseFilter[MessageCreated]):
    """Фильтр, который пишет в ctx, но не проходит."""

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        ctx["command"] = "start"
        return False


class SelfRefWritingFalseFilter(BaseFilter[MessageCreated]):
    """Фильтр, который пишет в ctx через self-ссылку, но не проходит."""

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        ctx[CTX_KEY]["command"] = "start"
        return False


@pytest.fixture
def bot() -> MockBot:
    return MockBot()


@pytest.fixture
def ctx(update: Any, bot: Bot) -> Ctx:
    ctx = Ctx({"update": update, "bot": bot})
    ctx["ctx"] = ctx
    return ctx
