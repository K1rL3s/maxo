import pytest

from maxo import Bot
from maxo.transport.webhook.security import Security, StaticSecret
from maxo.transport.webhook.security.secret import SECRET_HEADER
from tests.maxo_webhook.fixtures.web_request import DummyRequest, DummyWebRequest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("request_token", "expected"),
    [
        ("my-secret", True),
        ("wrong-secret", False),
        (None, False),
    ],
    ids=["match", "mismatch", "none"],
)
async def test_secret_check_verifies_telegram_header(
    request_token: str | None,
    expected: bool,
) -> None:
    secret = StaticSecret("my-secret")
    headers = {SECRET_HEADER: request_token} if request_token is not None else {}
    req = DummyWebRequest(DummyRequest(headers=headers))

    assert await secret.verify(request=req, route_params={}) is expected


@pytest.mark.parametrize("secret", ["", "has space", "x" * 257])
def test_secret_check_rejects_invalid_values(
    secret: str,
) -> None:
    with pytest.raises(ValueError, match="Invalid secret format"):
        StaticSecret(secret)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("secret", "expected"),
    [
        (StaticSecret("my-secret"), "my-secret"),
        (None, None),
    ],
    ids=["with-secret", "without-secret"],
)
async def test_security_resolves_secret_from_static_value_or_callable(
    bot: Bot,
    secret: StaticSecret | None,
    expected: str | None,
) -> None:
    sec = Security(secret=secret)
    assert await sec.secret(bot=bot) == expected
