try:
    from magic_filter import AttrDict, MagicFilter as OriginMagicFilter
except ImportError as e:
    e.add_note(" * Please run `pip install maxo[magic_filter]`")
    raise

from typing import Any

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter


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


class MagicFilter(BaseFilter[Any]):
    __slots__ = ("_magic_filter", "_result_key")

    def __init__(
        self,
        magic_filter: OriginMagicFilter,
        result_key: str | None = None,
    ) -> None:
        self._magic_filter = magic_filter
        self._result_key = result_key

    async def __call__(self, update: Any, ctx: Ctx) -> bool:
        result = self._magic_filter.resolve(update)
        if not result:
            return False

        if self._result_key is not None:
            ctx[self._result_key] = result

        return True
