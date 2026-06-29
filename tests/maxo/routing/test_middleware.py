from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest

from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import AlwaysFalseFilter, AlwaysTrueFilter, BaseFilter
from maxo.routing.interfaces import NextMiddleware
from maxo.routing.middlewares.fsm_context import FSMContextMiddleware
from maxo.routing.routers.simple import Router
from maxo.routing.sentinels import UNHANDLED
from maxo.routing.signals import BeforeStartup
from maxo.routing.updates.message_created import MessageCreated
from maxo.types import Message, MessageBody, Recipient, User


@pytest.fixture
def update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=datetime.now(UTC),
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=datetime.now(UTC),
            ),
        ),
        timestamp=datetime.now(UTC),
    )


async def handler(_: Any, ctx: Ctx) -> Any:
    ctx["execution_order"].append("handler")
    return "OK"


def middleware_factory(name: str) -> Callable[..., Any]:
    async def middleware(
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        ctx["execution_order"].append(f"{name}_pre")
        result = await next(ctx)
        ctx["execution_order"].append(f"{name}_post")
        return result

    return middleware


async def test_middleware_execution_order(ctx: Ctx) -> None:
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
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
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


async def test_middleware_stops_propagation(ctx: Ctx) -> None:
    dp = Dispatcher()

    async def stopping_middleware(
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        ctx["execution_order"].append("stopping_middleware")
        return "STOPPED"

    dp.message_created.middleware.outer.add(middleware_factory("outer"))
    dp.message_created.middleware.inner.add(stopping_middleware)
    dp.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "STOPPED"
    assert ctx["execution_order"] == [
        "outer_pre",
        "stopping_middleware",
        "outer_post",
    ]


async def test_outer_middleware_runs_if_filter_fails(ctx: Ctx) -> None:
    dp = Dispatcher()

    class UpdateFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("filter")
            return False

    dp.message_created.filter(UpdateFilter())
    dp.message_created.handler(handler)
    dp.message_created.middleware.outer.add(middleware_factory("outer"))

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == [
        "outer_pre",
        "filter",
        "outer_post",
    ]


async def test_nested_router_middleware_execution(ctx: Ctx) -> None:
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
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
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


async def test_router_filter_false_skips_router_inner_middleware(ctx: Ctx) -> None:
    dp = Dispatcher()
    router = Router("child")
    dp.include(router)

    class RouterFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("filter")
            return False

    router.message_created.filter(RouterFilter())
    router.message_created.middleware.inner.add(middleware_factory("inner"))
    router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == ["filter"]


async def test_router_filter_true_enters_router_inner_middleware(ctx: Ctx) -> None:
    dp = Dispatcher()
    router = Router("child")
    dp.include(router)

    class RouterFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("filter")
            return True

    router.message_created.filter(RouterFilter())
    router.message_created.middleware.inner.add(middleware_factory("inner"))
    router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
        "filter",
        "inner_pre",
        "handler",
        "inner_post",
    ]


async def test_first_router_inner_middleware_skipped_second_router_handles(
    ctx: Ctx,
) -> None:
    dp = Dispatcher()
    first_router = Router("first")
    second_router = Router("second")
    dp.include(first_router, second_router)

    class FirstRouterFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("first_filter")
            return False

    class SecondRouterFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("second_filter")
            return True

    async def second_handler(_: Any, ctx: Ctx) -> str:
        ctx["execution_order"].append("second_handler")
        return "OK"

    first_router.message_created.filter(FirstRouterFilter())
    first_router.message_created.middleware.inner.add(middleware_factory("first_inner"))
    second_router.message_created.filter(SecondRouterFilter())
    second_router.message_created.handler(second_handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
        "first_filter",
        "second_filter",
        "second_handler",
    ]


async def test_one_call_per_event_with_routers(ctx: Ctx) -> None:
    async def outer_middleware(
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
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
    ctx["calls"] = 0
    ctx["handler_calls"] = 0
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["calls"] == 1
    assert ctx["handler_calls"] == 1


async def test_fsm_disabled() -> None:
    dp = Dispatcher(disable_fsm=True)

    assert not any(
        isinstance(middleware, FSMContextMiddleware)
        for middleware in dp.update.middleware.outer.middlewares
    )


async def test_fsm_enabled_by_default() -> None:
    dp = Dispatcher()

    assert any(
        isinstance(m, FSMContextMiddleware)
        for m in dp.update.middleware.outer.middlewares
    )
