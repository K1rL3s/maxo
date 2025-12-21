from datetime import datetime
from typing import Any, Literal

import pytest

from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import AlwaysFalseFilter, AlwaysTrueFilter
from maxo.routing.routers.simple import Router
from maxo.routing.sentinels import UNHANDLED
from maxo.routing.signals import BeforeStartup
from maxo.routing.signals.update import Update
from maxo.routing.updates.message_created import MessageCreated
from maxo.types import Message, Recipient, User


class MockBotInfo:
    def __init__(self, user_id: int):
        self.user_id = user_id


class MockBotState:
    def __init__(self, user_id: int):
        self.info = MockBotInfo(user_id)


class MockBot:
    def __init__(self, user_id: int = 1):
        self.state = MockBotState(user_id)


@pytest.mark.asyncio
async def test_middleware_execution_order():
    dp = Dispatcher()

    async def handler(update, ctx) -> Any:
        ctx["execution_order"].append("handler")
        return "OK"

    async def outer_middleware_1(update, ctx, next) -> Any:
        ctx["execution_order"].append("outer_middleware_1_pre")
        result = await next(ctx)
        ctx["execution_order"].append("outer_middleware_1_post")
        return result

    async def outer_middleware_2(update, ctx, next) -> Any:
        ctx["execution_order"].append("outer_middleware_2_pre")
        result = await next(ctx)
        ctx["execution_order"].append("outer_middleware_2_post")
        return result

    async def inner_middleware_1(update, ctx, next) -> Any:
        ctx["execution_order"].append("inner_middleware_1_pre")
        result = await next(ctx)
        ctx["execution_order"].append("inner_middleware_1_post")
        return result

    async def inner_middleware_2(update, ctx, next) -> Any:
        ctx["execution_order"].append("inner_middleware_2_pre")
        result = await next(ctx)
        ctx["execution_order"].append("inner_middleware_2_post")
        return result

    dp.message_created.handler(handler)
    dp.message_created.middleware.outer.add(outer_middleware_1, outer_middleware_2)
    dp.message_created.middleware.inner.add(inner_middleware_1, inner_middleware_2)

    update = MessageCreated(
        message=Message(
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=datetime.now(),
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=datetime.now(),
            ),
        ),
        timestamp=datetime.now(),
    )
    ctx = Ctx({"execution_order": [], "update": update, "bot": MockBot()})
    ctx["ctx"] = ctx

    await dp.feed_signal(BeforeStartup())
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
        "outer_middleware_1_pre",
        "outer_middleware_2_pre",
        "inner_middleware_1_pre",
        "inner_middleware_2_pre",
        "handler",
        "inner_middleware_2_post",
        "inner_middleware_1_post",
        "outer_middleware_2_post",
        "outer_middleware_1_post",
    ]


@pytest.mark.asyncio
async def test_middleware_execution_before_observer_filter():
    dp = Dispatcher()

    async def update_filter(update, ctx) -> Literal[False]:
        ctx["execution_order"].append("filter")
        return False

    async def handler(update, ctx) -> Any:
        ctx["execution_order"].append("handler")
        return "OK"

    async def outer_middleware_1(update, ctx, next) -> Any:
        ctx["execution_order"].append("outer_middleware_1_pre")
        result = await next(ctx)
        ctx["execution_order"].append("outer_middleware_1_post")
        return result

    dp.message_created.filter(update_filter)
    dp.message_created.handler(handler)
    dp.message_created.middleware.outer.add(outer_middleware_1)

    update = MessageCreated(
        message=Message(
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=datetime.now(),
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=datetime.now(),
            ),
        ),
        timestamp=datetime.now(),
    )
    ctx = Ctx({"execution_order": [], "update": update, "bot": MockBot()})
    ctx["ctx"] = ctx

    await dp.feed_signal(BeforeStartup())
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == [
        "outer_middleware_1_pre",
        "filter",
        "outer_middleware_1_post",
    ]


@pytest.mark.asyncio
async def test_filter_on_update():
    dp = Dispatcher()

    async def update_filter(update, ctx) -> Literal[False]:
        ctx["execution_order"].append("filter")
        return False

    async def handler(update, ctx) -> Any:
        return "OK"

    dp.update.filter(update_filter)
    dp.message_created.handler(handler)

    update = Update(
        update=MessageCreated(
            message=Message(
                recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
                timestamp=datetime.now(),
                sender=User(
                    user_id=1,
                    first_name="Test",
                    is_bot=False,
                    last_activity_time=datetime.now(),
                ),
            ),
            timestamp=datetime.now(),
        ),
    )
    ctx = Ctx({"execution_order": [], "update": update, "bot": MockBot()})
    ctx["ctx"] = ctx

    await dp.feed_signal(BeforeStartup())
    result = await dp.trigger(ctx)

    assert result == UNHANDLED
    assert ctx["execution_order"] == [
        "filter",
    ]


@pytest.mark.asyncio
async def test_one_call_per_event() -> None:
    async def outer_middleware(update, ctx, next) -> Any:
        ctx["calls"] += 1
        return await next(ctx)

    dp = Dispatcher()
    dp.message_created.middleware.outer(outer_middleware)

    router1 = Router("1")
    router2 = Router("2")
    router3 = Router("3")

    dp.include(router1, router2, router3)

    @dp.message_created(AlwaysFalseFilter())
    @router1.message_created(AlwaysFalseFilter())
    @router2.message_created(AlwaysFalseFilter())
    @router3.message_created(AlwaysTrueFilter())
    async def handler(_: Any, ctx: Ctx) -> None:
        ctx["calls"] += 1_000_000

    update = MessageCreated(
        message=Message(
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=datetime.now(),
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=datetime.now(),
            ),
        ),
        timestamp=datetime.now(),
    )
    ctx = Ctx({"update": update, "bot": MockBot(), "calls": 0})
    ctx["ctx"] = ctx

    await dp.feed_signal(BeforeStartup())
    result = await dp.trigger(ctx)

    assert result is None
    assert ctx["calls"] == 1_000_001
