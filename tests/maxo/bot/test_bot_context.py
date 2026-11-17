from contextlib import nullcontext
from unittest.mock import AsyncMock

import pytest

from maxo import Bot


async def test_aenter_closes_client_when_me_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AsyncMock()
    bot = Bot("token", client=client)
    bot._owns_client = True

    async def boom() -> None:
        raise RuntimeError("bad token")

    monkeypatch.setattr(bot, "me", boom)
    with pytest.raises(RuntimeError):
        await bot.__aenter__()

    client.close.assert_awaited_once()


@pytest.mark.parametrize("auto_close", [True, False])
@pytest.mark.parametrize("fail_in", [None, "me", "body"])
async def test_deprecated_context_closes_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    auto_close: bool,
    fail_in: str | None,
) -> None:
    client = AsyncMock()
    bot = Bot("token", client=client)
    bot._owns_client = True
    me = AsyncMock(side_effect=RuntimeError("me") if fail_in == "me" else None)
    monkeypatch.setattr(bot, "me", me)

    with pytest.warns(DeprecationWarning, match="async with bot"):
        context = bot.context(auto_close=auto_close)

    expected = pytest.raises(RuntimeError, match=fail_in) if fail_in else nullcontext()
    with expected:
        async with context as entered:
            assert entered is bot
            client.close.assert_not_awaited()
            if fail_in == "body":
                raise RuntimeError("body")

    me.assert_awaited_once()
    assert client.close.await_count == int(auto_close)
