import functools
from typing import Any

from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.handlers.signal import SignalHandler
from maxo.routing.handlers.update import UpdateHandler
from maxo.types import Message, MessageBody, MessageCreated, Recipient
from tests.constants import NOW


class AsyncCallableHandler:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    async def __call__(self, update: Any, **kwargs: Any) -> str:
        self.calls.append(update)
        return "done"


class SyncCallableHandler:
    def __init__(self) -> None:
        self.calls: list[Any] = []

    def __call__(self, update: Any, **kwargs: Any) -> str:
        self.calls.append(update)
        return "done"


def decorator(fn: Any) -> Any:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    return wrapper


def make_update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=NOW,
        ),
        timestamp=NOW,
    )


async def handler_with_params(update: Any, bot: Any) -> Any:
    return bot


async def test_decorated_handler_receives_only_declared_params() -> None:
    handler = UpdateHandler[MessageCreated, Any](decorator(handler_with_params))

    ctx = Ctx({"update": make_update(), "bot": "bot", "extra": 1})

    assert await handler(ctx) == "bot"


async def test_class_based_update_handler_is_executed() -> None:
    handler_fn = AsyncCallableHandler()
    handler = UpdateHandler[MessageCreated, str](handler_fn)
    update = make_update()

    result = await handler(Ctx({"update": update}))

    assert result == "done"
    assert handler_fn.calls == [update]


async def test_sync_class_based_update_handler_is_executed() -> None:
    handler_fn = SyncCallableHandler()
    # синхронный вызываемый объект допустим в рантайме, но не по протоколу
    handler = UpdateHandler[MessageCreated, str](handler_fn)  # type: ignore[arg-type]
    update = make_update()

    result = await handler(Ctx({"update": update}))

    assert result == "done"
    assert handler_fn.calls == [update]


async def test_class_based_signal_handler_is_executed() -> None:
    handler_fn = AsyncCallableHandler()
    handler = SignalHandler[Any, str](handler_fn)

    assert await handler(Ctx({"update": None})) == "done"


class DecoratedCallableHandler:
    @decorator
    async def __call__(self, update: Any, **kwargs: Any) -> str:
        return "done"


async def test_decorated_call_class_based_handler_is_executed() -> None:
    handler = UpdateHandler[MessageCreated, str](DecoratedCallableHandler())

    assert await handler(Ctx({"update": make_update()})) == "done"
