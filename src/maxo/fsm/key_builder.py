"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/fsm/storage/base.py.

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

from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Protocol

DESTINY_DEFAULT: Final = "default"


@dataclass(frozen=True, slots=True)
class StorageKey:
    bot_id: int
    chat_id: int | None = None
    user_id: int | None = None
    destiny: str = DESTINY_DEFAULT


class StorageKeyType(StrEnum):
    DATA = "data"
    STATE = "state"
    LOCK = "lock"


class BaseKeyBuilder(Protocol):
    __slots__ = ()

    @abstractmethod
    def build(
        self,
        key: StorageKey,
        type_: StorageKeyType | None = None,
    ) -> str:
        raise NotImplementedError


class DefaultKeyBuilder(BaseKeyBuilder):
    __slots__ = ("prefix", "separator", "with_bot_id", "with_destiny")

    def __init__(
        self,
        *,
        prefix: str = "fsm",
        separator: str = ":",
        with_bot_id: bool = False,
        with_destiny: bool = False,
    ) -> None:
        self.prefix = prefix
        self.separator = separator
        self.with_bot_id = with_bot_id
        self.with_destiny = with_destiny

    def build(self, key: StorageKey, type_: StorageKeyType | None = None) -> str:
        parts = [self.prefix, str(key.chat_id), str(key.user_id)]

        if self.with_bot_id:
            parts.append(str(key.bot_id))

        if self.with_destiny:
            parts.append(key.destiny)
        elif key.destiny != DESTINY_DEFAULT:
            raise ValueError(
                f"Use `with_destiny=True` in for {self.__class__.__name__}",
            )

        if type_:
            parts.append(type_)

        return self.separator.join(parts)
