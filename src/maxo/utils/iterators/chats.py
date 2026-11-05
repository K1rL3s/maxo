from collections import deque
from collections.abc import AsyncIterator
from typing import Self

from typing_extensions import deprecated

from maxo.bot.bot import Bot
from maxo.omit import Omittable, Omitted
from maxo.types.chat import Chat


@deprecated("ChatsIterator ходит в GET /chats, который MAX не поддерживает с июня 2026")
class ChatsIterator(AsyncIterator[Chat]):
    _marker: Omittable[int | None]

    __slots__ = ("_bot", "_chats", "_count", "_marker")

    def __init__(
        self,
        bot: Bot,
        count: Omittable[int] = 50,
        marker: Omittable[int] = Omitted(),
    ) -> None:
        self._bot = bot
        self._count = count
        self._marker = marker

        self._chats: deque[Chat] = deque()

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> Chat:
        if self._chats:
            return self._chats.popleft()

        # `marker is None` - предыдущая страница была последней
        # Отдать такой маркер обратно нельзя:
        # для апи `marker: null` - это запрос первой страницы,
        # и итерация пойдёт по кругу
        if self._marker is None:
            raise StopAsyncIteration

        result = await self._bot.get_chats(count=self._count, marker=self._marker)

        if not result.chats:
            raise StopAsyncIteration

        self._chats.extend(result.chats)
        self._marker = result.marker

        return self._chats.popleft()
