from typing import Any, cast

from magic_filter import F

from maxo.integrations.magic_filter import MagicData, MagicFilter
from maxo.routing.ctx import Ctx


class TestMagicData:
    """`MagicData` резолвится по словарю `{"update": update, **ctx}`."""

    async def test_rejects_falsy_result(self) -> None:
        assert await MagicData(F.update["flag"])({"flag": False}, {}) is False  # type: ignore[arg-type]

    async def test_accepts_truthy_result(self) -> None:
        assert await MagicData(F.update["flag"])({"flag": True}, {}) is True  # type: ignore[arg-type]

    async def test_reads_value_from_ctx(self) -> None:
        ctx = cast(Ctx, {"role": "admin"})

        assert await MagicData(F.role == "admin")(object(), ctx) is True

    async def test_stores_result_in_ctx(self) -> None:
        ctx = cast(Ctx, {})

        assert await MagicData(F.update["value"], result_key="found")(
            {"value": 42},
            ctx,
        )
        assert ctx["found"] == 42


class TestMagicFilter:
    """`MagicFilter` резолвится прямо по апдейту."""

    async def test_rejects_falsy_result(self) -> None:
        assert await MagicFilter(F["flag"])({"flag": False}, {}) is False

    async def test_accepts_truthy_result(self) -> None:
        assert await MagicFilter(F["flag"])({"flag": True}, {}) is True

    async def test_stores_result_in_ctx(self) -> None:
        ctx: dict[str, Any] = {}

        assert await MagicFilter(F["value"], result_key="found")({"value": 7}, ctx)
        assert ctx["found"] == 7
