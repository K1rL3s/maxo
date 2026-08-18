from typing import cast
from unittest.mock import AsyncMock

import pytest

from maxo.routing.ctx import Ctx
from maxo.types import MessageCallback
from maxo.utils.callback_answer import (
    CALLBACK_ANSWER_KEY,
    CallbackAnswer,
    CallbackAnswerException,
    CallbackAnswerMiddleware,
)
from tests.factories import make_flagged_ctx


async def _next_ok(ctx: Ctx) -> str:
    return "OK"


async def test_answers_after_handler_by_default() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware()
    result = await mw(cast(MessageCallback, update), Ctx({}), _next_ok)
    assert result == "OK"
    update.answer.assert_awaited_once_with()


async def test_before_answers_before_handler() -> None:
    order: list[str] = []
    update = AsyncMock()
    update.answer = AsyncMock(side_effect=lambda **_: order.append("answer"))

    async def next_fn(ctx: Ctx) -> str:
        order.append("handler")
        return "OK"

    mw = CallbackAnswerMiddleware(before=True)
    await mw(cast(MessageCallback, update), Ctx({}), next_fn)
    assert order == ["answer", "handler"]


async def test_handler_can_disable() -> None:
    update = AsyncMock()

    async def next_fn(ctx: Ctx) -> str:
        ctx[CALLBACK_ANSWER_KEY].disabled = True
        return "OK"

    mw = CallbackAnswerMiddleware()
    await mw(cast(MessageCallback, update), Ctx({}), next_fn)
    update.answer.assert_not_awaited()


async def test_handler_can_change_notification() -> None:
    update = AsyncMock()

    async def next_fn(ctx: Ctx) -> str:
        ctx[CALLBACK_ANSWER_KEY].notification = "done"
        return "OK"

    mw = CallbackAnswerMiddleware()
    await mw(cast(MessageCallback, update), Ctx({}), next_fn)
    update.answer.assert_awaited_once_with(notification="done")


async def test_no_double_answer_when_before() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware(before=True)
    await mw(cast(MessageCallback, update), Ctx({}), _next_ok)
    update.answer.assert_awaited_once_with()


async def test_answers_even_when_handler_raises() -> None:
    update = AsyncMock()

    async def next_boom(ctx: Ctx) -> str:
        raise RuntimeError("boom")

    mw = CallbackAnswerMiddleware()
    with pytest.raises(RuntimeError, match="boom"):
        await mw(cast(MessageCallback, update), Ctx({}), next_boom)

    update.answer.assert_awaited_once_with()


async def test_disabled_handler_no_answer_on_exception() -> None:
    update = AsyncMock()

    async def next_boom(ctx: Ctx) -> str:
        ctx[CALLBACK_ANSWER_KEY].disabled = True
        raise RuntimeError("boom")

    mw = CallbackAnswerMiddleware()
    with pytest.raises(RuntimeError, match="boom"):
        await mw(cast(MessageCallback, update), Ctx({}), next_boom)

    update.answer.assert_not_awaited()


async def test_mutation_after_answer_raises() -> None:
    answer = CallbackAnswer(answered=True)

    with pytest.raises(CallbackAnswerException):
        answer.disabled = True
    with pytest.raises(CallbackAnswerException):
        answer.notification = "late"
    with pytest.raises(CallbackAnswerException):
        answer.before = True


async def test_mutation_before_answer_allowed() -> None:
    answer = CallbackAnswer()

    answer.disabled = True
    answer.notification = "ok"
    answer.before = True
    assert answer.disabled is True
    assert answer.notification == "ok"
    assert answer.before is True
    assert answer.answered is False


def test_exception_message() -> None:
    assert (
        str(CallbackAnswerException())
        == "Нельзя изменить CallbackAnswer после отправки ответа на колбэк"
    )


def test_disable_method() -> None:
    answer = CallbackAnswer()

    answer.disable()

    assert answer.disabled is True


async def test_flag_can_disable_answer() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware()

    await mw(
        cast(MessageCallback, update),
        make_flagged_ctx(callback_answer={"disabled": True}),
        _next_ok,
    )

    update.answer.assert_not_awaited()


async def test_flag_can_set_notification() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware()

    await mw(
        cast(MessageCallback, update),
        make_flagged_ctx(callback_answer={"notification": "Готово"}),
        _next_ok,
    )

    update.answer.assert_awaited_once_with(notification="Готово")


async def test_flag_can_set_before() -> None:
    order: list[str] = []
    update = AsyncMock()
    update.answer = AsyncMock(side_effect=lambda **_: order.append("answer"))

    async def next_fn(ctx: Ctx) -> str:
        order.append("handler")
        return "OK"

    mw = CallbackAnswerMiddleware()
    await mw(
        cast(MessageCallback, update),
        make_flagged_ctx(callback_answer={"before": True}),
        next_fn,
    )

    assert order == ["answer", "handler"]


async def test_false_flag_disables_answer() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware()

    await mw(
        cast(MessageCallback, update),
        make_flagged_ctx(callback_answer=False),
        _next_ok,
    )

    update.answer.assert_not_awaited()


async def test_true_flag_enables_disabled_middleware() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware(disabled=True)

    await mw(
        cast(MessageCallback, update),
        make_flagged_ctx(callback_answer=True),
        _next_ok,
    )

    update.answer.assert_awaited_once_with()


async def test_middleware_defaults_used_without_flag() -> None:
    update = AsyncMock()
    mw = CallbackAnswerMiddleware(notification="Дефолт")

    await mw(cast(MessageCallback, update), Ctx({}), _next_ok)

    update.answer.assert_awaited_once_with(notification="Дефолт")
