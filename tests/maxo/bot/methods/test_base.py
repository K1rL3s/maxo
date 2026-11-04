from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from maxo.backoff import BackoffConfig
from maxo.bot.api_client import MaxApiClient
from maxo.bot.methods import AddMembers, DeleteMessage  # type: ignore[deprecated]
from maxo.bot.methods.base import MaxoMethod
from maxo.bot.upload import UploadConfig
from maxo.errors import MaxBotBadRequestError
from maxo.serialization import create_retort
from maxo.types.modify_members_result import ModifyMembersResult
from tests.constants import TOKEN

from .conftest import response


def test_validate_response_ok() -> None:
    method: MaxoMethod[object] = MaxoMethod()
    http_response = response({"success": True})

    method.validate_response(http_response)

    assert http_response.status_code == 200


@pytest.mark.parametrize(
    "data",
    [
        {"success": False, "error_code": "some_error"},
        {"success": False},
        {"error_code": "some_error"},
    ],
)
def test_validate_response_error(data: dict[str, object]) -> None:
    method: MaxoMethod[object] = MaxoMethod()
    http_response = response(data)

    with pytest.raises(MaxBotBadRequestError) as exc_info:
        method.validate_response(http_response)

    assert exc_info.value.raw_data == data
    assert http_response.status_code == 200


def test_validate_response_ignores_non_dict_body() -> None:
    method: MaxoMethod[object] = MaxoMethod()

    method.validate_response(response("plain text"))


def test_validate_response_ignores_error_statuses() -> None:
    method: MaxoMethod[object] = MaxoMethod()

    method.validate_response(response({"success": False}, status_code=500))


def test_add_members_keeps_partial_result() -> None:
    http_response = response({"success": False, "error_code": "some_error"})

    AddMembers(chat_id=1, user_ids=[2]).validate_response(http_response)

    assert http_response.status_code == 200


@pytest.fixture
async def api_client() -> AsyncIterator[MaxApiClient]:
    retort = create_retort(warming_up=False)
    client = MaxApiClient(token=TOKEN, request_dumper=retort, response_loader=retort)
    yield client
    await client.close()


async def test_call_method_raises_on_success_false(api_client: MaxApiClient) -> None:
    body = {"success": False, "message": "denied"}
    api_client.make_request = AsyncMock(return_value=response(body))  # type: ignore[method-assign]

    with pytest.raises(MaxBotBadRequestError) as exc_info:
        await api_client.call_method(DeleteMessage(message_id="m1"))

    assert exc_info.value.raw_data == body


async def test_call_method_returns_add_members_partial_result(
    api_client: MaxApiClient,
) -> None:
    body = {"success": False, "message": "partial", "failed_user_ids": [2]}
    api_client.make_request = AsyncMock(return_value=response(body))  # type: ignore[method-assign]

    result = await api_client.call_method(AddMembers(chat_id=1, user_ids=[2, 3]))

    assert isinstance(result, ModifyMembersResult)
    assert result.success is False
    assert result.failed_user_ids == [2]


async def test_not_ready_error_in_success_false_body_is_retried() -> None:
    retort = create_retort(warming_up=False)
    fast_backoff = BackoffConfig(min_delay=0.0, max_delay=0.01, factor=2.0, jitter=0.0)
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=retort,
        response_loader=retort,
        upload_config=UploadConfig(not_ready_backoff=fast_backoff),
    )
    not_ready = {"success": False, "error_code": "attachment.not.ready"}
    client.make_request = AsyncMock(  # type: ignore[method-assign]
        side_effect=[response(not_ready), response({"success": True})],
    )
    try:
        result = await client.call_method(DeleteMessage(message_id="m1"))
    finally:
        await client.close()

    assert result.success is True
    assert client.make_request.await_count == 2
