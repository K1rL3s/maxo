try:
    from magic_filter import AttrDict, MagicFilter as OriginMagicFilter
    from magic_filter.operations import BaseOperation, CallOperation
except ImportError as e:
    e.add_note(" * Please run `pip install maxo[magic_filter]`")
    raise

from collections.abc import Mapping, Sequence
from typing import Any, Final

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces.filter import Filter

__all__ = ("F", "MagicData", "MagicFilter")

# `(update, ctx)` - столько аргументов у вызова фильтра
_FILTER_CALL_ARGS: Final = 2


class MagicData(BaseFilter[Any]):
    __slots__ = ("_magic_filter", "_result_key")

    def __init__(
        self,
        magic_filter: OriginMagicFilter,
        result_key: str | None = None,
    ) -> None:
        self._magic_filter = magic_filter
        self._result_key = result_key

    async def __call__(self, update: Any, ctx: Ctx) -> bool:
        result = self._magic_filter.resolve(AttrDict({"update": update, **ctx}))
        if not result:
            return False

        if self._result_key is not None:
            ctx[self._result_key] = result

        return True


def _is_maxo_filter(value: Any) -> bool:
    """Фильтр `maxo`, но не магия: магию комбинируем по правилам `magic_filter`."""
    return isinstance(value, Filter) and not isinstance(value, OriginMagicFilter)


class MagicFilter(OriginMagicFilter, BaseFilter[Any]):
    """
    Магия `magic_filter`, которая одновременно является фильтром `maxo`.

    Любой узел магии - и `F.text`, и `F.text == "hi"` - это `MagicFilter`,
    поэтому его можно передавать прямо в хендлер:

        ```python
        @router.message_created(F.text == "hi")
        async def handler(update: MessageCreated) -> None: ...


        @router.message_created(F.message.body.text)  # "есть текст"
        async def any_text(update: MessageCreated) -> None: ...
        ```

    Как фильтр магия резолвится по апдейту, а результат приводится к `bool`.
    Если задан `result_key`, результат кладется в контекст под этим именем и
    доезжает до хендлера как аргумент.
    """

    __slots__ = ("_result_key",)

    def __init__(
        self,
        operations: Sequence[BaseOperation] | OriginMagicFilter = (),
        result_key: str | None = None,
    ) -> None:
        if isinstance(operations, OriginMagicFilter):
            # `MagicFilter(F.text == "hi")` - обертка вокруг чужой магии
            operations = operations._operations  # noqa: SLF001

        super().__init__(tuple(operations))
        self._result_key = result_key

    # Магия занимает `__call__` под `CallOperation` (`F.text.casefold()`), а
    # фильтр вызывается как `(update, ctx)`. Отличаем по аргументам: вызов с
    # ровно двумя позиционными, где второй - контекст, считаем вызовом фильтра.
    # В цепочке магии такой вызов означал бы метод с mapping во втором аргументе -
    # на практике таких не бывает.
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if self._is_filter_call(args, kwargs):
            return self._check(*args)

        return self._extend(CallOperation(args=args, kwargs=kwargs))

    @staticmethod
    def _is_filter_call(args: tuple[Any, ...], kwargs: dict[str, Any]) -> bool:
        return (
            not kwargs
            and len(args) == _FILTER_CALL_ARGS
            and isinstance(args[1], Mapping)
        )

    async def _check(self, update: Any, ctx: Ctx) -> bool:
        result = self.resolve(update)
        if not result:
            return False

        if self._result_key is not None:
            ctx[self._result_key] = result

        return True

    # Магия комбинируется с магией по правилам `magic_filter`, а с обычным
    # фильтром `maxo` - через `AndFilter` / `OrFilter`.
    def __and__(self, other: Any) -> Any:
        if _is_maxo_filter(other):
            return BaseFilter.__and__(self, other)

        return OriginMagicFilter.__and__(self, other)

    def __or__(self, other: Any) -> Any:
        if _is_maxo_filter(other):
            return BaseFilter.__or__(self, other)

        return OriginMagicFilter.__or__(self, other)


F = MagicFilter()
