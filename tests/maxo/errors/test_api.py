import pytest

from maxo.errors import (
    MaxBotApiError,
    MaxBotBadGatewayError,
    MaxBotBadRequestError,
    MaxBotClientError,
    MaxBotForbiddenError,
    MaxBotMethodNotAllowedError,
    MaxBotNotFoundError,
    MaxBotResponseError,
    MaxBotServerError,
    MaxBotServiceUnavailableError,
    MaxBotTooManyRequestsError,
    MaxBotUnauthorizedError,
    MaxBotUnknownServerError,
    MaxBotUnsupportedMediaTypeError,
)
from maxo.errors.api import raise_api_error


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
        (502, MaxBotBadGatewayError),
        (503, MaxBotServiceUnavailableError),
        (418, MaxBotClientError),
        (501, MaxBotServerError),
        (302, MaxBotApiError),
    ],
)
def test_raise_api_error_falls_back_to_status_group(
    status_code: int,
    error_class: type[MaxBotApiError],
) -> None:
    with pytest.raises(error_class):
        raise_api_error(status_code, {})


def test_api_error_str_uses_fields_and_raw_data() -> None:
    error = MaxBotApiError("code", "error", "message")
    raw_error = MaxBotApiError("", "", "", {"raw": "data"})
    status_error = MaxBotApiError("", "", "", b"<html>", 502)

    assert str(error) == (
        "MaxBotApiError(code='code', error='error', message='message')"
    )
    assert str(raw_error) == "MaxBotApiError(raw_data={'raw': 'data'})"
    assert str(status_error) == "MaxBotApiError(status_code=502, raw_data=b'<html>')"


@pytest.mark.parametrize(
    ("data", "message"),
    [(b"<html>Bad Gateway</html>", "<html>Bad Gateway</html>"), (None, "")],
)
def test_raise_api_error_without_json_body_keeps_status_and_text(
    data: object,
    message: str,
) -> None:
    with pytest.raises(MaxBotBadGatewayError) as exc_info:
        raise_api_error(502, data)

    assert exc_info.value.status_code == 502
    assert exc_info.value.error == ""
    assert exc_info.value.message == message


def test_raise_api_error_reads_dict_body() -> None:
    data = {"error_code": "proto.payload", "error_data": None, "message": 1}

    with pytest.raises(MaxBotBadRequestError) as exc_info:
        raise_api_error(400, data)

    error = exc_info.value
    assert (error.code, error.error, error.message) == ("proto.payload", "", "1")
    assert error.status_code == 400
    assert error.raw_data is data


def test_response_error_str() -> None:
    assert str(MaxBotResponseError(method="GetChat")) == "Неожиданный ответ GetChat"
    assert str(MaxBotResponseError(method="UploadMedia", detail="нет токена")) == (
        "Неожиданный ответ UploadMedia: нет токена"
    )
