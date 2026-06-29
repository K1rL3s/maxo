import pytest

from maxo import Bot
from maxo.omit import Omitted
from maxo.transport.webhook.security import Security, StaticSecretToken
from maxo.transport.webhook.security.secret_token import SECRET_HEADER

from .fixtures import DummyBoundRequest, DummyRequest


@pytest.mark.parametrize(
    ("secret_token", "request_token", "expected"),
    [
        ("my-secret", "my-secret", True),
        ("my-secret", "wrong-secret", False),
        ("my-secret", None, False),
    ],
    ids=["match", "mismatch", "none"],
)
async def test_security_secret_token(
    secret_token: str,
    request_token: str | None,
    expected: bool,
    bot: Bot,
) -> None:
    sec = Security(secret_token=StaticSecretToken(secret_token))
    headers = {SECRET_HEADER: request_token} if request_token is not None else {}
    req = DummyBoundRequest(DummyRequest(headers=headers))
    assert await sec.verify(bot, req) is expected


@pytest.mark.parametrize(
    ("secret_token", "expected"),
    [
        (StaticSecretToken("test-secret"), "test-secret"),
        (None, Omitted()),
    ],
    ids=["with-secret", "without-secret"],
)
async def test_security_get_secret_token(
    secret_token: StaticSecretToken | None,
    expected: str | None,
    bot: Bot,
) -> None:
    sec = Security(secret_token=secret_token)
    assert await sec.get_secret_token(bot=bot) == expected
