from typing import Any

import pytest

from maxo.enums import ChatType
from maxo.routing.ctx import CTX_KEY, Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import AlwaysFalseFilter, BaseFilter
from maxo.routing.routers.simple import Router
from maxo.routing.sentinels import UNHANDLED, SkipHandler
from maxo.routing.signals import BeforeStartup
from maxo.types import Message, MessageBody, Recipient, User
from maxo.types.message_created import MessageCreated
from tests.constants import NOW

from .conftest import SelfRefWritingFalseFilter, WritingFalseFilter, WritingFilter


@pytest.fixture
def update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=NOW,
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=NOW,
            ),
        ),
        timestamp=NOW,
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


async def test_handler_multiple_filters_all_true_runs_handler(ctx: Ctx) -> None:
    dp = Dispatcher()

    class FirstFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("first_filter")
            return True

    class SecondFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("second_filter")
            return True

    dp.message_created.handler(handler, FirstFilter(), SecondFilter())

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == ["first_filter", "second_filter", "handler"]


async def test_register_multiple_filters_all_true_runs_handler(ctx: Ctx) -> None:
    dp = Dispatcher()

    class FirstFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("first_filter")
            return True

    class SecondFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("second_filter")
            return True

    dp.message_created.register(handler, FirstFilter(), SecondFilter())

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == ["first_filter", "second_filter", "handler"]


async def test_handler_multiple_filters_one_false_skips_handler(ctx: Ctx) -> None:
    dp = Dispatcher()

    class FirstFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("first_filter")
            return True

    class SecondFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("second_filter")
            return False

    dp.message_created.handler(handler, FirstFilter(), SecondFilter())

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == ["first_filter", "second_filter"]


async def test_observer_multiple_filters_combined_as_and(ctx: Ctx) -> None:
    dp = Dispatcher()

    class FirstFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("first_filter")
            return True

    class SecondFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("second_filter")
            return False

    dp.message_created.filter(FirstFilter(), SecondFilter())
    dp.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result is UNHANDLED
    assert ctx["execution_order"] == ["first_filter", "second_filter"]


async def test_decorator_multiple_filters_combined_as_and(ctx: Ctx) -> None:
    dp = Dispatcher()

    class FirstFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("first_filter")
            return True

    class SecondFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            ctx["execution_order"].append("second_filter")
            return True

    @dp.message_created(FirstFilter(), SecondFilter())
    async def decorated_handler(_: Any, ctx: Ctx) -> str:
        ctx["execution_order"].append("handler")
        return "OK"

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == ["first_filter", "second_filter", "handler"]


async def test_handler_no_filters_runs_handler(ctx: Ctx) -> None:
    dp = Dispatcher()

    dp.message_created.handler(handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert ctx["execution_order"] == ["handler"]


async def test_failed_handler_filter_chain_does_not_leak_ctx(ctx: Ctx) -> None:
    dp = Dispatcher()

    leaked: dict[str, bool] = {}

    async def fallback_handler(_: Any, ctx: Ctx) -> str:
        leaked["command"] = "command" in ctx
        return "OK"

    dp.message_created.handler(handler, WritingFilter(), AlwaysFalseFilter())
    dp.message_created.handler(fallback_handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert leaked["command"] is False
    assert "command" not in ctx


async def test_failed_child_router_filter_does_not_leak_ctx(ctx: Ctx) -> None:
    dp = Dispatcher()
    first_child = Router("first_child")
    second_child = Router("second_child")
    dp.include(first_child)
    dp.include(second_child)

    leaked: dict[str, bool] = {}

    async def fallback_handler(_: Any, ctx: Ctx) -> str:
        leaked["command"] = "command" in ctx
        return "OK"

    first_child.message_created.filter(WritingFilter(), AlwaysFalseFilter())
    first_child.message_created.handler(handler)
    second_child.message_created.handler(fallback_handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert leaked["command"] is False
    assert "command" not in ctx


async def test_failed_single_handler_filter_does_not_leak_ctx(ctx: Ctx) -> None:
    dp = Dispatcher()

    leaked: dict[str, bool] = {}

    async def fallback_handler(_: Any, ctx: Ctx) -> str:
        leaked["command"] = "command" in ctx
        return "OK"

    dp.message_created.handler(handler, WritingFalseFilter())
    dp.message_created.handler(fallback_handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert leaked["command"] is False
    assert "command" not in ctx


async def test_failed_filter_does_not_leak_ctx_through_self_reference(ctx: Ctx) -> None:
    dp = Dispatcher()

    leaked: dict[str, bool] = {}

    async def fallback_handler(_: Any, ctx: Ctx) -> str:
        leaked["command"] = "command" in ctx
        return "OK"

    dp.message_created.handler(handler, SelfRefWritingFalseFilter())
    dp.message_created.handler(fallback_handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert leaked["command"] is False
    assert "command" not in ctx
    assert ctx[CTX_KEY] is ctx


async def test_failed_single_child_router_filter_does_not_leak_ctx(ctx: Ctx) -> None:
    dp = Dispatcher()
    first_child = Router("first_child")
    second_child = Router("second_child")
    dp.include(first_child)
    dp.include(second_child)

    leaked: dict[str, bool] = {}

    async def fallback_handler(_: Any, ctx: Ctx) -> str:
        leaked["command"] = "command" in ctx
        return "OK"

    first_child.message_created.filter(WritingFalseFilter())
    first_child.message_created.handler(handler)
    second_child.message_created.handler(fallback_handler)

    await dp.feed_signal(BeforeStartup())
    ctx["execution_order"] = []
    result = await dp.trigger(ctx)

    assert result == "OK"
    assert leaked["command"] is False
    assert "command" not in ctx


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
