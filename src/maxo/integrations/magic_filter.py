try:
    from magic_filter import AttrDict, MagicFilter as OriginMagicFilter
    from magic_filter.operations import BaseOperation, CallOperation
except ImportError as e:
    e.add_note(" * Please run `pip install maxo[magic_filter]`")
    raise

from collections.abc import MutableMapping, Sequence
from typing import Any, Final
from warnings import warn

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces.filter import Filter

__all__ = ("F", "MagicData", "MagicFilter")

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
    return isinstance(value, Filter) and not isinstance(value, OriginMagicFilter)


class MagicFilter(OriginMagicFilter, BaseFilter[Any]):
    """
    Магия `magic_filter`, которая одновременно является фильтром `maxo`.

    Любой узел магии - и `F.text`, и `F.text == "hi"` - можно передать в хендлер.
    Как фильтр магия резолвится по апдейту, результат приводится к `bool`.
    `result_key` кладет результат в контекст, и он доезжает до хендлера аргументом.
    """

    __slots__ = ("_result_key",)

    __hash__ = object.__hash__

    def __init__(
        self,
        operations: Sequence[BaseOperation] | OriginMagicFilter = (),
        result_key: str | None = None,
    ) -> None:
        if isinstance(operations, OriginMagicFilter):
            warn(
                "MagicFilter(...) устарел; передавайте F-выражение напрямую.",
                DeprecationWarning,
                stacklevel=2,
            )
            operations = operations._operations  # noqa: SLF001

        super().__init__(tuple(operations))
        self._result_key = result_key

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        if len(args) == _FILTER_CALL_ARGS and isinstance(args[1], MutableMapping):
            return self._check(args[0], args[1])

        return self._extend(CallOperation(args=args, kwargs=kwargs))

    # magic_filter объявляет `_new` classmethod, но result_key принадлежит узлу.
    def _new(  # type: ignore[override]
        self,
        operations: tuple[BaseOperation, ...],
    ) -> "MagicFilter":
        return type(self)(operations, result_key=self._result_key)

    async def _check(self, update: Any, ctx: MutableMapping[str, Any]) -> bool:
        result = self.resolve(update)
        if not result:
            return False

        if self._result_key is not None:
            ctx[self._result_key] = result

        return True

    # С магией комбинируемся по правилам `magic_filter`, чтобы результат остался
    # магией, с обычным фильтром `maxo` - через `AndFilter` / `OrFilter`.
    def __and__(self, other: Any) -> Any:
        if _is_maxo_filter(other):
            return BaseFilter.__and__(self, other)

        return OriginMagicFilter.__and__(self, other)

    def __or__(self, other: Any) -> Any:
        if _is_maxo_filter(other):
            return BaseFilter.__or__(self, other)

        return OriginMagicFilter.__or__(self, other)


F = MagicFilter()
