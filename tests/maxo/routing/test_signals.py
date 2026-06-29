from datetime import UTC, datetime

import pytest

from maxo import Bot, Router
from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.middlewares.state import (
    EmptyMiddlewareManagerState,
    StartedMiddlewareManagerState,
)
from maxo.routing.observers.state import EmptyObserverState, StartedObserverState
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
    MaxoUpdate,
)
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
