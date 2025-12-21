from datetime import datetime
from typing import Any

import pytest

from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import AlwaysFalseFilter, AlwaysTrueFilter
from maxo.routing.routers.simple import Router
from maxo.routing.sentinels import UNHANDLED
from maxo.routing.signals import BeforeStartup
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


@pytest.fixture
def bot() -> MockBot:
    return MockBot()


@pytest.fixture
def message_created_update() -> MessageCreated:
    return MessageCreated(
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


@pytest.fixture
def context(message_created_update: MessageCreated, bot: MockBot) -> Ctx:
    ctx = Ctx({"update": message_created_update, "bot": bot})
    ctx["ctx"] = ctx
    return ctx


async def handler(_: Any, ctx: Ctx) -> Any:
    ctx["execution_order"].append("handler")
    return "OK"


def middleware_factory(name: str):
    async def middleware(update, ctx, next) -> Any:
        ctx["execution_order"].append(f"{name}_pre")
        result = await next(ctx)
        ctx["execution_order"].append(f"{name}_post")
        return result

    return middleware


@pytest.mark.asyncio
async def test_middleware_execution_order(context: Ctx):
    dp = Dispatcher()

    dp.message_created.handler(handler)
    dp.message_created.middleware.outer.add(
        middleware_factory("outer_1"),
        middleware_factory("outer_2"),
    )
    dp.message_created.middleware.inner.add(
        middleware_factory("inner_1"),
        middleware_factory("inner_2"),
    )

    await dp.feed_signal(BeforeStartup())
    context["execution_order"] = []
    result = await dp.trigger(context)

    assert result == "OK"
    assert context["execution_order"] == [
        "outer_1_pre",
        "outer_2_pre",
        "inner_1_pre",
        "inner_2_pre",
        "handler",
        "inner_2_post",
        "inner_1_post",
        "outer_2_post",
        "outer_1_post",
    ]


@pytest.mark.asyncio
async def test_middleware_stops_propagation(context: Ctx):
    dp = Dispatcher()

    async def stopping_middleware(update, ctx, next) -> Any:
        ctx["execution_order"].append("stopping_middleware")
        return "STOPPED"

    dp.message_created.middleware.outer.add(middleware_factory("outer"))
    dp.message_created.middleware.inner.add(stopping_middleware)
    dp.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    context["execution_order"] = []
    result = await dp.trigger(context)

    assert result == "STOPPED"
    assert context["execution_order"] == [
        "outer_pre",
        "stopping_middleware",
        "outer_post",
    ]


@pytest.mark.asyncio
async def test_outer_middleware_runs_if_filter_fails(context: Ctx):
    dp = Dispatcher()

    async def update_filter(_: Any, ctx: Ctx) -> bool:
        ctx["execution_order"].append("filter")
        return False

    dp.message_created.filter(update_filter)
    dp.message_created.handler(handler)
    dp.message_created.middleware.outer.add(middleware_factory("outer"))

    await dp.feed_signal(BeforeStartup())
    context["execution_order"] = []
    result = await dp.trigger(context)

    assert result is UNHANDLED
    assert context["execution_order"] == [
        "outer_pre",
        "filter",
        "outer_post",
    ]


@pytest.mark.asyncio
async def test_nested_router_middleware_execution(context: Ctx):
    dp = Dispatcher()
    root_router = Router("root")
    child_router = Router("child")
    dp.include(root_router)
    root_router.include(child_router)

    dp.message_created.middleware.outer.add(middleware_factory("dp"))
    root_router.message_created.middleware.outer.add(middleware_factory("root"))
    child_router.message_created.middleware.outer.add(middleware_factory("child"))
    child_router.message_created.middleware.inner.add(middleware_factory("inner"))

    child_router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    context["execution_order"] = []
    result = await dp.trigger(context)

    assert result == "OK"
    assert context["execution_order"] == [
        "dp_pre",
        "root_pre",
        "child_pre",
        "inner_pre",
        "handler",
        "inner_post",
        "child_post",
        "root_post",
        "dp_post",
    ]


@pytest.mark.asyncio
async def test_one_call_per_event_with_routers(context: Ctx) -> None:
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
    async def successful_handler(_: Any, ctx: Ctx) -> str:
        ctx["handler_calls"] += 1
        return "OK"

    await dp.feed_signal(BeforeStartup())
    context["calls"] = 0
    context["handler_calls"] = 0
    result = await dp.trigger(context)

    assert result == "OK"
    assert context["calls"] == 1
    assert context["handler_calls"] == 1
