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
