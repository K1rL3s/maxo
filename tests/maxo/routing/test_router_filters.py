from datetime import UTC, datetime
from typing import Any

import pytest

from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.routers.simple import Router
from maxo.routing.sentinels import UNHANDLED, SkipHandler
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


async def handler(_: Any, ctx: Ctx) -> str:
    ctx["execution_order"].append("handler")
    return "OK"


async def skipping_handler(_: Any, ctx: Ctx) -> None:
    ctx["execution_order"].append("skipping_handler")
    raise SkipHandler


async def test_parent_included_router_filter_false_blocks_child_router(
    ctx: Ctx,
) -> None:
    dp = Dispatcher()
    parent_router = Router("parent")
    child_router = Router("child")
    dp.include(parent_router)
    parent_router.include(child_router)

    class ParentFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("parent_filter")
            return False

    class ChildFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("child_filter")
            return True

    parent_router.message_created.filter(ParentFilter())
    child_router.message_created.filter(ChildFilter())
    child_router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == ["parent_filter"]


async def test_parent_and_child_included_router_filters_allow_handler(ctx: Ctx) -> None:
    dp = Dispatcher()
    parent_router = Router("parent")
    child_router = Router("child")
    dp.include(parent_router)
    parent_router.include(child_router)

    class ParentFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("parent_filter")
            return True

    class ChildFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("child_filter")
            return True

    parent_router.message_created.filter(ParentFilter())
    child_router.message_created.filter(ChildFilter())
    child_router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
        "parent_filter",
        "child_filter",
        "handler",
    ]


async def test_child_filter_false_stops_after_parent_filter(ctx: Ctx) -> None:
    dp = Dispatcher()
    parent_router = Router("parent")
    child_router = Router("child")
    dp.include(parent_router)
    parent_router.include(child_router)

    class ParentFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("parent_filter")
            return True

    class ChildFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("child_filter")
            return False

    parent_router.message_created.filter(ParentFilter())
    child_router.message_created.filter(ChildFilter())
    child_router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == [
        "parent_filter",
        "child_filter",
    ]


async def test_dispatcher_filter_false_blocks_included_routers(ctx: Ctx) -> None:
    dp = Dispatcher()
    child_router = Router("child")
    dp.include(child_router)

    class DispatcherFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("dispatcher_filter")
            return False

    class ChildFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("child_filter")
            return True

    dp.message_created.filter(DispatcherFilter())
    child_router.message_created.filter(ChildFilter())
    child_router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == ["dispatcher_filter"]


async def test_parent_handlers_filtered_out_falls_through_to_child(ctx: Ctx) -> None:
    dp = Dispatcher()
    parent_router = Router("parent")
    child_router = Router("child")
    dp.include(parent_router)
    parent_router.include(child_router)

    class ParentFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("parent_filter")
            return True

    class ParentHandlerFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("parent_handler_filter")
            return False

    class ChildFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("child_filter")
            return True

    parent_router.message_created.filter(ParentFilter())
    parent_router.message_created.handler(handler, ParentHandlerFilter())
    child_router.message_created.filter(ChildFilter())
    child_router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
        "parent_filter",
        "parent_handler_filter",
        "child_filter",
        "handler",
    ]


async def test_skip_handler_in_parent_falls_through_to_child(ctx: Ctx) -> None:
    dp = Dispatcher()
    parent_router = Router("parent")
    child_router = Router("child")
    dp.include(parent_router)
    parent_router.include(child_router)

    class ParentFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("parent_filter")
            return True

    class ChildFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("child_filter")
            return True

    parent_router.message_created.filter(ParentFilter())
    parent_router.message_created.handler(skipping_handler)
    child_router.message_created.filter(ChildFilter())
    child_router.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == [
        "parent_filter",
        "skipping_handler",
        "child_filter",
        "handler",
    ]
