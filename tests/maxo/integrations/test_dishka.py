from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from dishka import (
    FromDishka,
    Provider,
    Scope,
    make_async_container,
    provide,
)

from maxo import Bot, Dispatcher
from maxo.enums import ChatType
from maxo.integrations.dishka import setup_dishka
from maxo.routing.signals.startup import BeforeStartup
from maxo.routing.signals.update import MaxoUpdate
from maxo.routing.updates import MessageCreated
from maxo.types import Message, MessageBody, Recipient


class MyService:
    def do_something(self) -> str:
        return "done"


class MyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_service(self) -> MyService:
        return MyService()


@pytest.fixture
def update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=datetime.now(UTC),
        ),
        timestamp=datetime.now(UTC),
    )


@pytest.fixture
def bot() -> Bot:
    return MagicMock(spec=Bot)


async def test_dishka_auto_inject(update: MessageCreated, bot: Bot):
    # 1. Create dependencies
    service_mock = MagicMock(spec=MyService)
    service_mock.do_something.return_value = "mocked_done"

    class TestProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_service(self) -> MyService:
            return service_mock

    # 2. Create container
    container = make_async_container(TestProvider())

    # 3. Create dispatcher
    dp = Dispatcher()

    # 4. Connect them
    setup_dishka(container, dp, auto_inject=True)

    # 5. Define handler
    handler_mock = AsyncMock()

    @dp.message_created()
    async def my_handler(
        _: MessageCreated,
        service: FromDishka[MyService],
    ) -> None:
        await handler_mock(service.do_something())

    # 7. Trigger dispatcher startup and then trigger
    await dp.feed_signal(BeforeStartup())
    await dp.feed_max_update(MaxoUpdate(update=update), bot)

    # 8. Assert
    handler_mock.assert_awaited_once_with("mocked_done")
    await container.close()


async def test_dishka_no_auto_inject(update: MessageCreated, bot: Bot) -> None:
    # This test checks that without auto_inject=True, the handler does not get the dependency

    # 1. Create dependencies
    class TestProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_service(self) -> MyService:
            return MyService()

    # 2. Create container
    container = make_async_container(TestProvider())

    # 3. Create dispatcher
    dp = Dispatcher()

    # 4. Connect them
    setup_dishka(container, dp, auto_inject=False)

    # 5. Define handler with injection
    handler_mock = AsyncMock()

    @dp.message_created()
    async def my_handler(
        message: MessageCreated,
        service: FromDishka[MyService],
    ):
        await handler_mock(service.do_something())

    # 7. Trigger dispatcher
    await dp.feed_signal(BeforeStartup())
    with pytest.raises(TypeError):
        await dp.feed_update(update, bot)

    # 8. Assert
    handler_mock.assert_not_awaited()
    await container.close()
