import pytest

from maxo.transport.webhook.security.errors import SecretError, SecurityCheckError
from maxo.transport.webhook.security.secret import SECRET_HEADER, StaticSecret
from maxo.transport.webhook.security.security import Security
from tests.maxo_webhook.fixtures.security_checks import RecordingCheck
from tests.maxo_webhook.fixtures.web_request import DummyRequest, DummyWebRequest


@pytest.mark.asyncio
async def test_security_verify_noop_without_checks_or_secret() -> None:
    security = Security()

    await security.verify(request=DummyWebRequest(), route_params={})


@pytest.mark.asyncio
async def test_security_pipeline_stops_at_first_failed_check() -> None:
    calls: list[str] = []
    security = Security(
        RecordingCheck("first", result=True, calls=calls),
        RecordingCheck("second", result=False, calls=calls),
        RecordingCheck("third", result=True, calls=calls),
    )
    request = DummyWebRequest(DummyRequest(ip="127.0.0.1"))

    with pytest.raises(SecurityCheckError) as exc_info:
        await security.verify(request=request, route_params={})

    assert calls == ["first", "second"]
    assert exc_info.value.security_check == "RecordingCheck"
    assert exc_info.value.client_ip == "127.0.0.1"


@pytest.mark.asyncio
async def test_security_pipeline_allows_request_when_secret_and_checks_pass() -> None:
    calls: list[str] = []
    security = Security(
        RecordingCheck("check", result=True, calls=calls),
        secret=StaticSecret("secret"),
    )
    request = DummyWebRequest(DummyRequest(headers={SECRET_HEADER: "secret"}))

    await security.verify(request=request, route_params={})

    assert calls == ["check"]


@pytest.mark.asyncio
async def test_security_pipeline_runs_checks_after_valid_secret() -> None:
    calls: list[str] = []
    security = Security(
        RecordingCheck("check", result=False, calls=calls),
        secret=StaticSecret("secret"),
    )
    request = DummyWebRequest(DummyRequest(headers={SECRET_HEADER: "secret"}))

    with pytest.raises(SecurityCheckError):
        await security.verify(request=request, route_params={})

    assert calls == ["check"]


@pytest.mark.asyncio
async def test_security_pipeline_rejects_bad_secret_before_checks() -> None:
    calls: list[str] = []
    security = Security(
        RecordingCheck("check", result=True, calls=calls),
        secret=StaticSecret("secret"),
    )
    request = DummyWebRequest(DummyRequest(headers={SECRET_HEADER: "wrong"}))

    with pytest.raises(SecretError):
        await security.verify(request=request, route_params={})

    assert calls == []
