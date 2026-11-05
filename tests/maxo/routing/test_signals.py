from typing import Any

import pytest

from maxo import Bot, Router
from maxo.enums import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.middlewares.state import (
    EmptyMiddlewareManagerState,
    StartedMiddlewareManagerState,
)
from maxo.routing.observers.state import EmptyObserverState, StartedObserverState
from maxo.routing.sentinels import SkipHandler
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
    MaxoUpdate,
)
from maxo.types import Message, MessageBody, Recipient, User
from maxo.types.error_event import ErrorEvent
from maxo.types.message_created import MessageCreated
from tests.constants import NOW


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


async def test_dp_signals() -> None:
    dp = Dispatcher()
    order = []

    @dp.before_startup()
    async def before_startup() -> None:
        order.append("before_startup")

    @dp.after_startup()
    async def after_startup() -> None:
        order.append("after_startup")

    @dp.before_shutdown()
    async def before_shutdown() -> None:
        order.append("before_shutdown")

    @dp.after_shutdown()
    async def after_shutdown() -> None:
        order.append("after_shutdown")

    await dp.feed_signal(BeforeStartup())
    await dp.feed_signal(AfterStartup())
    await dp.feed_signal(BeforeShutdown())
    await dp.feed_signal(AfterShutdown())

    assert order == [
        "before_startup",
        "after_startup",
        "before_shutdown",
        "after_shutdown",
    ]


async def test_included_router_signals() -> None:
    dp = Dispatcher()
    deep_router = Router()
    deeper_router = Router()
    deepest_router = Router()

    dp.include(deep_router)
    deep_router.include(deeper_router)
    deeper_router.include(deepest_router)

    order = []

    @dp.before_startup()
    @deep_router.before_startup()
    @deeper_router.before_startup()
    @deepest_router.before_startup()
    async def before_startup() -> None:
        order.append("before_startup")

    @dp.after_startup()
    @deep_router.after_startup()
    async def after_startup() -> None:
        order.append("after_startup")

    @deep_router.before_shutdown()
    @deeper_router.before_shutdown()
    async def before_shutdown() -> None:
        order.append("before_shutdown")

    @deeper_router.after_shutdown()
    @deepest_router.after_shutdown()
    async def after_shutdown() -> None:
        order.append("after_shutdown")

    await dp.feed_signal(BeforeStartup())
    await dp.feed_signal(AfterStartup())
    await dp.feed_signal(BeforeShutdown())
    await dp.feed_signal(AfterShutdown())

    assert order == [
        *(["before_startup"] * 4),
        *(["after_startup"] * 2),
        *(["before_shutdown"] * 2),
        *(["after_shutdown"] * 2),
    ]


async def test_included_router_observers_state() -> None:
    # ruff: noqa: E721
    dp = Dispatcher()
    deep_router = Router()
    deeper_router = Router()

    dp.include(deep_router)
    deep_router.include(deeper_router)

    for router in (dp, deep_router, deeper_router):
        for observer in router.observers.values():
            assert type(observer.state) == EmptyObserverState
            assert type(observer.middleware.inner.state) == EmptyMiddlewareManagerState

    await dp.feed_signal(BeforeStartup())

    for router in (dp, deep_router, deeper_router):
        for observer in router.observers.values():
            assert type(observer.state) == StartedObserverState
            assert (
                type(observer.middleware.inner.state) == StartedMiddlewareManagerState
            )

    await dp.feed_signal(AfterStartup())
    await dp.feed_signal(BeforeShutdown())

    for router in (dp, deep_router, deeper_router):
        for observer in router.observers.values():
            assert type(observer.state) == EmptyObserverState
            assert type(observer.middleware.inner.state) == EmptyMiddlewareManagerState

    await dp.feed_signal(AfterShutdown())


async def test_dp_update_handler(update: MessageCreated, bot: Bot) -> None:
    dp = Dispatcher()

    triggered = False

    @dp.update()
    async def update_handler(update: MaxoUpdate[MessageCreated]) -> None:
        assert isinstance(update, MaxoUpdate)
        assert isinstance(update.update, MessageCreated)
        nonlocal triggered
        triggered = True

    await dp.feed_signal(BeforeStartup())
    await dp.feed_signal(AfterStartup())

    await dp.feed_max_update(MaxoUpdate(update=update), bot)
    assert triggered


async def test_signal_filter_false_blocks_handler() -> None:
    dp = Dispatcher()
    order = []

    class BeforeStartupFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("filter")
            return False

    dp.before_startup.filter(BeforeStartupFilter())

    @dp.before_startup()
    async def before_startup() -> None:
        order.append("handler")

    await dp.feed_signal(BeforeStartup())

    assert order == ["filter"]


async def test_signal_filter_called_once() -> None:
    dp = Dispatcher()
    order = []

    class BeforeStartupFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("filter")
            return True

    dp.before_startup.filter(BeforeStartupFilter())

    @dp.before_startup()
    async def before_startup() -> None:
        order.append("handler")

    await dp.feed_signal(BeforeStartup())

    assert order == ["filter", "handler"]


async def test_signal_handler_multiple_filters_all_true_runs_handler() -> None:
    dp = Dispatcher()
    order = []

    class FirstFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("first_filter")
            return True

    class SecondFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("second_filter")
            return True

    async def before_startup() -> None:
        order.append("handler")

    dp.before_startup.handler(before_startup, FirstFilter(), SecondFilter())

    await dp.feed_signal(BeforeStartup())

    assert order == ["first_filter", "second_filter", "handler"]


async def test_signal_register_multiple_filters_all_true_runs_handler() -> None:
    dp = Dispatcher()
    order = []

    class FirstFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("first_filter")
            return True

    class SecondFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("second_filter")
            return True

    async def before_startup() -> None:
        order.append("handler")

    dp.before_startup.register(before_startup, FirstFilter(), SecondFilter())

    await dp.feed_signal(BeforeStartup())

    assert order == ["first_filter", "second_filter", "handler"]


async def test_signal_handler_multiple_filters_one_false_skips_handler() -> None:
    dp = Dispatcher()
    order = []

    class FirstFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("first_filter")
            return True

    class SecondFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("second_filter")
            return False

    async def before_startup() -> None:
        order.append("handler")

    dp.before_startup.handler(before_startup, FirstFilter(), SecondFilter())

    await dp.feed_signal(BeforeStartup())

    assert order == ["first_filter", "second_filter"]


async def test_observer_filter_multiple_filters_combined_as_and() -> None:
    dp = Dispatcher()
    order = []

    class FirstFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("first_filter")
            return True

    class SecondFilter(BaseFilter[BeforeStartup]):
        async def __call__(self, update: BeforeStartup, ctx: Ctx) -> bool:
            order.append("second_filter")
            return False

    dp.before_startup.filter(FirstFilter(), SecondFilter())

    @dp.before_startup()
    async def before_startup() -> None:
        order.append("handler")

    await dp.feed_signal(BeforeStartup())

    assert order == ["first_filter", "second_filter"]


async def test_feed_update_does_not_bind_bot(update: MessageCreated, bot: Bot) -> None:
    dp = Dispatcher()
    handled = []

    @dp.message_created()
    async def handler(update: MessageCreated) -> None:
        handled.append(update)

    await dp.feed_signal(BeforeStartup())
    maxo_update = MaxoUpdate(update=update)
    await dp.feed_update(maxo_update, bot)

    assert handled == [update]
    with pytest.raises(AttributeIsEmptyError):
        _ = maxo_update.bot
    with pytest.raises(AttributeIsEmptyError):
        _ = update.bot


async def test_signal_skip_handler_runs_next_handlers() -> None:
    dp = Dispatcher()
    router = Router()
    dp.include(router)
    order = []

    @dp.after_startup()
    async def skipped() -> None:
        order.append("skipped")
        raise SkipHandler

    @dp.after_startup()
    async def next_handler() -> None:
        order.append("next_handler")

    @router.after_startup()
    async def child_handler() -> None:
        order.append("child_handler")

    await dp.feed_signal(BeforeStartup())
    await dp.feed_signal(AfterStartup())

    assert order == ["skipped", "next_handler", "child_handler"]


async def test_signal_exception_bypasses_error_handlers(bot: Bot) -> None:
    dp = Dispatcher()
    errors = []

    @dp.error()
    async def on_error(event: ErrorEvent[Exception, Any]) -> None:
        errors.append(event)

    @dp.after_startup()
    async def failing() -> None:
        raise ValueError("boom")

    await dp.feed_signal(BeforeStartup(), bot)
    with pytest.raises(ValueError, match="boom"):
        await dp.feed_signal(AfterStartup(), bot)

    assert errors == []
