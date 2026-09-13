from http.cookies import SimpleCookie
from unittest.mock import AsyncMock

import pytest
from multidict import CIMultiDict
from unihttp.http import HTTPResponse, UploadFile

from maxo.bot.methods.upload.upload_media import UploadMedia
from maxo.errors import RetvalReturnedError


def response(data: object) -> HTTPResponse:
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


def test_retval_response_raises_retval_returned_error() -> None:
    with pytest.raises(RetvalReturnedError, match="POST /uploads"):
        method().validate_response(response(b"<retval>1</retval>"))


def test_token_response_passes_validation() -> None:
    method().validate_response(response({"token": "file-token"}))
