"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/dispatcher/flags.py.

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

import inspect
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, cast, overload

from maxo.omit import Omitted, is_omitted
from maxo.routing.interfaces.filter import Filter

if TYPE_CHECKING:
    from maxo.routing.interfaces.handler import Handler

    FlagsSource = Handler[Any, Any] | MutableMapping[str, Any] | None

FLAG_ATTR_NAME: Final = "maxo_flag"

HANDLER_KEY: Final = "handler"


class AttrDict(dict[str, Any]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    if TYPE_CHECKING:
        # Имена атрибутов определяются в рантайме
        def __getattr__(self, name: str) -> Any: ...


@dataclass(frozen=True, slots=True)
class Flag:
    name: str
    value: Any


@dataclass(frozen=True, slots=True)
class FlagDecorator:
    flag: Flag

    def _with_value(self, value: Any) -> "FlagDecorator":
        return FlagDecorator(Flag(self.flag.name, value))

    @overload
    def __call__(self, value: Callable[..., Any], /) -> Callable[..., Any]: ...

    @overload
    def __call__(self, value: Any, /) -> "FlagDecorator": ...

    @overload
    def __call__(self, **kwargs: Any) -> "FlagDecorator": ...

    def __call__(
        self,
        value: Any = Omitted(),
        **kwargs: Any,
    ) -> "Callable[..., Any] | FlagDecorator":
        value_is_omitted = is_omitted(value)
        if not value_is_omitted and kwargs:
            raise ValueError(
                "Аргументы `value` и `**kwargs` нельзя использовать вместе",
            )

        if not value_is_omitted and callable(value):
            setattr(
                value,
                FLAG_ATTR_NAME,
                {
                    **extract_flags_from_object(value),
                    self.flag.name: self.flag.value,
                },
            )
            return cast(Callable[..., Any], value)

        return self._with_value(AttrDict(kwargs) if value_is_omitted else value)


class FlagGenerator:
    """Создаёт декораторы флагов через атрибуты."""

    __slots__ = ()

    def __getattr__(self, name: str) -> FlagDecorator:
        if name.startswith("_"):
            raise AttributeError("Имя флага не должно начинаться с подчёркивания")
        return FlagDecorator(Flag(name=name, value=True))


flags = FlagGenerator()
"""Генератор декораторов флагов"""


def extract_flags_from_object(obj: Any) -> dict[str, Any]:
    """Возвращает флаги, добавленные декораторами."""
    obj_flags = getattr(obj, FLAG_ATTR_NAME, None)
    if obj_flags is None:
        return {}
    return cast(dict[str, Any], obj_flags)


def resolve_handler_flags(
    handler_fn: Callable[..., Any],
    filters: Sequence[Filter[Any]] = (),
    flags: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved: dict[str, Any] = dict(flags) if flags else {}

    for filter_ in filters:
        update_handler_flags = getattr(filter_, "update_handler_flags", None)
        if update_handler_flags is not None:
            update_handler_flags(resolved)

    # Поддерживаем оба порядка декораторов
    resolved.update(extract_flags_from_object(inspect.unwrap(handler_fn)))
    resolved.update(extract_flags_from_object(handler_fn))
    return resolved


def extract_flags(source: "FlagsSource") -> dict[str, Any]:
    """Возвращает флаги из хендлера или `ctx`."""
    if isinstance(source, (dict, MutableMapping)) and HANDLER_KEY in source:
        source = source[HANDLER_KEY]

    source_flags = getattr(source, "flags", None)
    if source_flags is None:
        return {}
    return cast(dict[str, Any], source_flags)


def get_flag(
    source: "FlagsSource",
    name: str,
    *,
    default: Any | None = None,
) -> Any:
    """Возвращает значение флага или `default`."""
    return extract_flags(source).get(name, default)
