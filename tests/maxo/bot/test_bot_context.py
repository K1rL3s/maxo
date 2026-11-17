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


@pytest.mark.parametrize("auto_close", [None, True, False])
@pytest.mark.parametrize("owned", [True, False])
async def test_context_closes_only_owned_client_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    auto_close: bool | None,
    owned: bool,
) -> None:
    client = AsyncMock()
    bot = Bot("token", client=client, warming_up=False)
    bot._owns_client = owned
    me = AsyncMock()
    monkeypatch.setattr(bot, "me", me)

    context = bot.context() if auto_close is None else bot.context(auto_close)
    async with context as entered:
        assert entered is bot
        me.assert_awaited_once()
        client.close.assert_not_awaited()

    assert client.close.await_count == int(owned and auto_close is not False)


@pytest.mark.parametrize("auto_close", [True, False])
async def test_context_closes_after_body_failure_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    auto_close: bool,
) -> None:
    client = AsyncMock()
    bot = Bot("token", client=client, warming_up=False)
    bot._owns_client = True
    monkeypatch.setattr(bot, "me", AsyncMock())

    with pytest.raises(RuntimeError, match="body failed"):
        async with bot.context(auto_close):
            raise RuntimeError("body failed")

    assert client.close.await_count == int(auto_close)


@pytest.mark.parametrize("auto_close", [True, False])
async def test_context_closes_after_initialization_failure_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    auto_close: bool,
) -> None:
    client = AsyncMock()
    bot = Bot("token", client=client, warming_up=False)
    bot._owns_client = True
    monkeypatch.setattr(bot, "me", AsyncMock(side_effect=RuntimeError("bad token")))

    with pytest.raises(RuntimeError, match="bad token"):
        async with bot.context(auto_close):
            pytest.fail("context body must not run")

    assert client.close.await_count == int(auto_close)
