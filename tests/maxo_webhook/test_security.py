import pytest

from maxo import Bot
from maxo.transport.webhook.security import SecurityCheck
from maxo.transport.webhook.security.secret_token import (
    SECRET_HEADER,
    StaticSecretToken,
)
from maxo.transport.webhook.security.security import Security

from .fixtures import DummyBoundRequest, DummyRequest, FailingCheck, PassingCheck


@pytest.mark.parametrize(
    ("checks", "expected"),
    [
        # No checks - should pass
        ([], True),
        # Single check
        ([PassingCheck()], True),
        ([FailingCheck()], False),
        # Two checks
        ([PassingCheck(), PassingCheck()], True),
        ([PassingCheck(), FailingCheck()], False),
        ([FailingCheck(), PassingCheck()], False),
        ([FailingCheck(), FailingCheck()], False),
        # Three+ checks
        ([PassingCheck(), PassingCheck(), PassingCheck()], True),
        ([FailingCheck(), PassingCheck(), PassingCheck()], False),
        ([PassingCheck(), PassingCheck(), FailingCheck()], False),
    ],
    ids=[
        "no-checks",
        "single-passing",
        "single-failing",
        "two-passing",
        "passing-then-failing",
        "failing-then-passing",
        "two-failing",
        "three-passing",
        "failing-first-passing",
        "failing-last-passing",
    ],
)
async def test_security_checks(
    checks: list[SecurityCheck],
    expected: bool,
    bot: Bot,
) -> None:
    sec = Security(*checks)
    req = DummyBoundRequest()
    assert await sec.verify(bot, req) is expected


@pytest.mark.parametrize(
    ("checks", "secret_token", "request_token", "expected"),
    [
        # Both present and working
        ([PassingCheck()], StaticSecretToken("secret"), "secret", True),
        ([FailingCheck()], StaticSecretToken("secret"), "secret", False),
        ([PassingCheck()], StaticSecretToken("secret"), "wrong", False),
        # No checks
        ([], StaticSecretToken("secret"), "secret", True),
        ([], StaticSecretToken("secret"), "wrong", False),
        # No secret token
        ([PassingCheck()], None, None, True),
        ([FailingCheck()], None, None, False),
        # No checks and no secret token
        ([], None, None, True),
    ],
    ids=[
        "both-pass",
        "check-fails",
        "secret-fails",
        "no-checks-secret-pass",
        "no-checks-secret-fail",
        "no-secret-check-pass",
        "no-secret-check-fail",
        "no-checks-no-secret",
    ],
)
async def test_security_checks_and_secret_token(
    checks: list[SecurityCheck],
    secret_token: StaticSecretToken | None,
    request_token: str | None,
    expected: bool,
    bot: Bot,
) -> None:
    sec = Security(*checks, secret_token=secret_token)
    headers = {SECRET_HEADER: request_token} if request_token is not None else {}
    req = DummyBoundRequest(DummyRequest(headers=headers))
    assert await sec.verify(bot, req) is expected
