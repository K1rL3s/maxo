from http.cookies import SimpleCookie
from unittest.mock import AsyncMock

import pytest
from multidict import CIMultiDict
from unihttp.http import HTTPResponse, UploadFile

from maxo.bot.methods.upload.upload_media import UploadMedia
from maxo.errors import MaxBotBadRequestError
from maxo.serialization import get_retort
from maxo.types.upload_media_result import UploadMediaResult


def response(data: object) -> HTTPResponse[object]:
    return HTTPResponse(
        status_code=200,
        data=data,
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )


def method() -> UploadMedia:
    return UploadMedia(
        upload_url="https://example.com",
        file=UploadFile(file=b"video", filename="video.mp4"),
    )


def test_retval_response_returns_none() -> None:
    resp = response(b"<retval>1</retval>")

    method().validate_response(resp)

    assert method().make_response(resp, get_retort()) is None


def test_error_in_ok_body_raises_bad_request() -> None:
    resp = response({"error_code": "upload.error", "message": "nope"})

    with pytest.raises(MaxBotBadRequestError, match="nope"):
        method().validate_response(resp)


def test_token_response_is_loaded() -> None:
    resp = response({"token": "file-token"})

    method().validate_response(resp)

    assert method().make_response(resp, get_retort()) == UploadMediaResult(
        token="file-token",  # noqa: S106
    )
