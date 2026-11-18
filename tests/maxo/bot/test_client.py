import ssl
from typing import Any

import pytest
from aiohttp import ClientSession, ClientTimeout

from maxo.bot.client import default_client


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ssl_context": ssl.create_default_context()},
        {"limit": 10},
        {"timeout": ClientTimeout(total=1)},
    ],
)
async def test_session_with_session_options_raises(kwargs: dict[str, Any]) -> None:
    async with ClientSession() as session:
        with pytest.raises(TypeError, match="can't be used with `session`"):
            default_client(session=session, **kwargs)


async def test_own_session_is_used_as_is() -> None:
    async with ClientSession() as session:
        client = default_client(session=session)
        assert client._session is session


async def test_built_session_gets_options() -> None:
    timeout = ClientTimeout(total=1)
    client = default_client(limit=10, timeout=timeout)
    try:
        assert client._session.timeout is timeout
        assert client._session.connector is not None
        assert client._session.connector.limit == 10
    finally:
        await client.close()
