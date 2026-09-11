from http.cookies import SimpleCookie
from typing import Any
from unittest.mock import AsyncMock

import pytest
from multidict import CIMultiDict
from unihttp.http import HTTPResponse

from maxo.bot.methods import AddMembers
from maxo.bot.methods.base import MaxoMethod
from maxo.errors import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotForbiddenError,
    MaxBotMethodNotAllowedError,
    MaxBotNotFoundError,
    MaxBotServiceUnavailableError,
    MaxBotTooManyRequestsError,
    MaxBotUnauthorizedError,
    MaxBotUnknownServerError,
    MaxBotUnsupportedMediaTypeError,
)


@pytest.mark.parametrize(
    ("status_code", "error_class"),
    [
        (400, MaxBotBadRequestError),
        (401, MaxBotUnauthorizedError),
        (403, MaxBotForbiddenError),
        (404, MaxBotNotFoundError),
        (405, MaxBotMethodNotAllowedError),
        (415, MaxBotUnsupportedMediaTypeError),
        (429, MaxBotTooManyRequestsError),
        (500, MaxBotUnknownServerError),
        (502, MaxBotApiError),
        (503, MaxBotServiceUnavailableError),
    ],
)
def test_on_error(status_code: int, error_class: type[MaxBotApiError]) -> None:
    response: HTTPResponse[dict[str, Any]] = HTTPResponse(
        status_code=status_code,
        data={},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()
    with pytest.raises(error_class):
        method.on_error(response)


def test_on_error_with_non_dict_payload() -> None:
    response = HTTPResponse(
        status_code=502,
        data="plain error",
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()

    with pytest.raises(MaxBotApiError) as exc_info:
        method.on_error(response)

    assert exc_info.value.raw_data == "plain error"


def test_on_error_converts_none_message() -> None:
    response = HTTPResponse(
        status_code=400,
        data={"message": None},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()

    with pytest.raises(MaxBotBadRequestError) as exc_info:
        method.on_error(response)

    assert exc_info.value.message == ""


def test_validate_response_ok() -> None:
    response = HTTPResponse(
        status_code=200,
        data={"success": True},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()
    method.validate_response(response)
    assert response.status_code == 200


def test_validate_response_error() -> None:
    response = HTTPResponse(
        status_code=200,
        data={"success": False, "error_code": "some_error"},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()
    method.validate_response(response)
    assert response.status_code == 400


def test_validate_response_preserves_add_members_result() -> None:
    response = HTTPResponse(
        status_code=200,
        data={"success": False, "error_code": "some_error"},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )

    AddMembers(chat_id=1, user_ids=[2]).validate_response(response)

    assert response.status_code == 200
