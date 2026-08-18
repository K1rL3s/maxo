"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/utils/callback_answer.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

from collections.abc import Mapping
from typing import Any

from maxo.errors import MaxoError
from maxo.routing.ctx import Ctx
from maxo.routing.flags import get_flag
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.types import MessageCallback

CALLBACK_ANSWER_KEY = "callback_answer"


class CallbackAnswerException(MaxoError):
    """Попытка изменить `CallbackAnswer` после того, как ответ уже отправлен."""

    def __str__(self) -> str:
        return "Нельзя изменить CallbackAnswer после отправки ответа на колбэк"


class CallbackAnswer:
    """
    Управление авто-ответом на колбэк из хендлера.

    Middleware кладёт объект в ctx под ключом `CALLBACK_ANSWER_KEY`.
    Хендлер, объявивший параметр `callback_answer: CallbackAnswer`,
    может его мутировать до того, как middleware ответит
    """

    __slots__ = ("_answered", "_before", "_disabled", "_notification")

    def __init__(
        self,
        *,
        disabled: bool = False,
        before: bool = False,
        notification: str | None = None,
        answered: bool = False,
    ) -> None:
        self._disabled = disabled
        self._before = before
        self._notification = notification
        self._answered = answered

    @property
    def answered(self) -> bool:
        """Внутреннее: ответ уже отправлен (только для чтения)."""
        return self._answered

    @property
    def disabled(self) -> bool:
        """Не отвечать на этот колбэк."""
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._raise_if_answered()
        self._disabled = value

    @property
    def before(self) -> bool:
        """Ответить до хендлера, а не после."""
        return self._before

    @before.setter
    def before(self, value: bool) -> None:
        self._raise_if_answered()
        self._before = value

    @property
    def notification(self) -> str | None:
        """Текст одноразового уведомления (иначе пустой ответ)."""
        return self._notification

    @notification.setter
    def notification(self, value: str | None) -> None:
        self._raise_if_answered()
        self._notification = value

    def disable(self) -> None:
        """Отключить авто-ответ на этот колбэк."""
        self.disabled = True

    def _raise_if_answered(self) -> None:
        if self._answered:
            raise CallbackAnswerException


class CallbackAnswerMiddleware(BaseMiddleware[MessageCallback]):
    """Отвечает на колбэк с учётом флага `callback_answer`."""

    __slots__ = ("_before", "_disabled", "_notification")

    def __init__(
        self,
        before: bool = False,
        disabled: bool = False,
        notification: str | None = None,
    ) -> None:
        self._before = before
        self._disabled = disabled
        self._notification = notification

    async def __call__(
        self,
        update: MessageCallback,
        ctx: Ctx,
        next: NextMiddleware[MessageCallback],
    ) -> Any:
        answer = self.construct_callback_answer(get_flag(ctx, CALLBACK_ANSWER_KEY))
        ctx[CALLBACK_ANSWER_KEY] = answer

        if answer.before and not answer.disabled:
            await self._answer(update, answer)

        try:
            return await next(ctx)
        finally:
            if not answer.disabled and not answer.answered:
                await self._answer(update, answer)

    def construct_callback_answer(self, properties: Any) -> CallbackAnswer:
        disabled, before, notification = (
            self._disabled,
            self._before,
            self._notification,
        )

        if properties is None:
            return CallbackAnswer(
                disabled=disabled,
                before=before,
                notification=notification,
            )

        if isinstance(properties, Mapping):
            disabled = properties.get("disabled", disabled)
            before = properties.get("before", before)
            notification = properties.get("notification", notification)
        elif isinstance(properties, bool):
            disabled = not properties

        return CallbackAnswer(
            disabled=disabled,
            before=before,
            notification=notification,
        )

    async def _answer(self, update: MessageCallback, answer: CallbackAnswer) -> None:
        if answer.notification is not None:
            await update.answer(notification=answer.notification)
        else:
            await update.answer()
        answer._answered = True  # noqa: SLF001 - объект принадлежит мидлвари
